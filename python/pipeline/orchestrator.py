from dataclasses import dataclass
from .sentiment import SentimentEngine
from .conversation_analysis import analyze_conversation
from .validation import assert_valid_payload
from .knowledge import extract_knowledge, validate_and_learn
from datetime import datetime, timezone
import hashlib, re, unicodedata

@dataclass
class PipelineConfig:
    schema_version:str="1.3.0"
    processing_version:str="1.0.0"
    rules_version:str="1.0.0"
    quality_thresholds:tuple=(0.8,0.5)
    sentiment_allow_fallback:bool=True

RULES={
    "logistica":["retraso","no llega","paquete","entrega"],
    "servicio":["atencion","soporte","servicio"],
    "facturacion":["cobro","factura","cargo"],
    "tecnico":["error","falla","bug","no funciona"],
    "elogio":["excelente","genial","gracias","me encanta"],
}

def clean_text(text):
    text=unicodedata.normalize("NFKC",str(text))
    text=re.sub(r"https?://\S+"," [URL] ",text)
    text=re.sub(r"[\t\r\n]+"," ",text)
    text=re.sub(r"\s+"," ",text).strip()
    return text

def quality(text):
    if not text: return "invalida"
    if len(text)<4: return "baja"
    if len(text)>=20: return "alta"
    return "media"

def classify_rule(text):
    low=text.lower()
    hits=[name for name,terms in RULES.items() if any(term in low for term in terms)]
    return hits or ["otro"]

def heuristic_sentiment(text):
    # Fallback deterministic only for environments without pysentimiento.
    low=text.lower()
    positive=["excelente","genial","gracias","me encanta","bueno","feliz"]
    negative=["malo","horrible","retraso","error","falla","no funciona","queja"]
    p=sum(t in low for t in positive); n=sum(t in low for t in negative)
    if p>n:return "positivo",min(1,p/3)
    if n>p:return "negativo",min(1,n/3)
    return "neutro",0.34

def score(sentiment,rules,text):
    base={"positivo":15,"neutro":40,"negativo":65}[sentiment]
    urgency=15 if any(x in text.lower() for x in ["urgente","hoy","crítico","grave"]) else 0
    category=10 if rules[0] in {"logistica","facturacion","tecnico"} else 0
    value=min(100,base+urgency+category)
    severity="critica" if value>=85 else "alta" if value>=65 else "media" if value>=45 else "baja"
    return value,severity,[{"factor":"sentimiento","value":base},{"factor":"urgencia","value":urgency},{"factor":"categoria","value":category}]

class Pipeline:
    def __init__(self,config):
        self.config=config
        self.sentiment_engine=SentimentEngine(allow_fallback=config.sentiment_allow_fallback)
    def run(self,rows):
        now=datetime.now(timezone.utc).isoformat()
        mentions=[]; seen=set(); conversations={}
        for i,row in enumerate(rows):
            original=str(row.get("texto_original",row.get("texto",""))).strip()
            translated=str(row.get("texto_traducido",row.get("translated_text",""))).strip()
            analysis_text=translated or original
            cleaned=clean_text(analysis_text)
            source=str(row.get("fuente","unknown"))
            date=str(row.get("fecha",now))
            canonical=f"{source}|{date}|{cleaned.lower()}"
            h=hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            duplicate=h in seen; seen.add(h)
            sentiment,confidence,score_sentiment=self.sentiment_engine.predict(cleaned)
            rules=classify_rule(cleaned)
            sc,sev,factors=score(sentiment,rules,cleaned)
            conversation_id = str(row.get("conversation_id") or f"conv-{source}-{hashlib.sha256(source.encode('utf-8')).hexdigest()[:12]}")
            speaker = str(row.get("speaker", ""))
            speaker_role = str(row.get("speaker_role", "desconocido" if speaker else "no_atribuido"))
            turn_index = int(row.get("turn_index") or (len(conversations.get(conversation_id, {}).get("turns", [])) + 1))
            conversations.setdefault(conversation_id, {"conversation_id":conversation_id,"fuente":source,"turns":[],"participants":{}})
            conversations[conversation_id]["turns"].append({"turn_index":turn_index,"mention_id":str(row.get("id_mencion", f"M-{i+1:06d}")),"speaker":speaker,"speaker_role":speaker_role})
            if speaker:
                conversations[conversation_id]["participants"].setdefault(speaker, {"speaker":speaker,"speaker_role":speaker_role,"turns":0,"sentiments":{}})
                conversations[conversation_id]["participants"][speaker]["turns"] += 1
                conversations[conversation_id]["participants"][speaker]["sentiments"][sentiment] = conversations[conversation_id]["participants"][speaker]["sentiments"].get(sentiment, 0) + 1
            mentions.append({
                "id_mencion":str(row.get("id_mencion",f"M-{i+1:06d}")),
                "hash_mencion":h,"fuente":source,"fecha":date,
                "texto_original":original,"texto_traducido":translated or None,"texto_limpio":cleaned,
                "sentimiento_pysentimiento":sentiment,"score_sentimiento":score_sentiment,
                "confianza_sentimiento":confidence,"entidad_detectada":row.get("entidad_detectada"),"idioma_origen":row.get("idioma_origen",""),"idioma_analisis":row.get("idioma_analisis") or ("es" if translated else row.get("idioma_origen","")),"metodo_traduccion":row.get("metodo_traduccion","manual" if translated else "no_aplicado"),"speaker":row.get("speaker",""),"conversation_id":conversation_id,"turn_index":turn_index,"speaker_role":speaker_role,
                "categoria":rules[0],"subcategoria":"","regla_activada":rules[0],
                "reglas_activadas":rules,"prioridad_regla":len(rules),"factores_score":factors,
                "score_matematico":sc,"severidad":sev,"calidad_dato":quality(cleaned),
                "es_duplicado":duplicate,"tiene_error":not bool(cleaned),
                "advertencias":["DUPLICADO_HASH"] if duplicate else [],
                "procesado_en":now,"version_procesamiento":self.config.processing_version,
                "version_reglas":self.config.rules_version,"version_schema":self.config.schema_version
            })
        conversation_list=[]
        for conv in conversations.values():
            participant_values=[]
            for part in conv["participants"].values():
                participant_values.append(part)
            conv["participants"] = participant_values
            conv["turn_count"] = len(conv["turns"])
            conv["sentiment_counts"] = {s: sum(1 for m in mentions if m.get("conversation_id") == conv["conversation_id"] and m.get("sentimiento_pysentimiento") == s) for s in ["positivo","negativo","neutro"]}
            conv["unattributed_turns"] = sum(1 for t in conv["turns"] if t.get("speaker_role") == "no_atribuido")
            by_id = {m["id_mencion"]: m for m in mentions if m.get("conversation_id") == conv["conversation_id"]}
            conv["analysis"] = analyze_conversation(conv, by_id)
            conversation_list.append(conv)
        stats={"total":len(mentions),
               "sentiment_counts":{s:sum(m["sentimiento_pysentimiento"]==s for m in mentions) for s in ["positivo","negativo","neutro"]},"conversation_count":len(conversation_list),"participant_count":sum(len(c["participants"]) for c in conversation_list)}
        knowledge=validate_and_learn(extract_knowledge(conversation_list, {m["id_mencion"]: m for m in mentions}))
        result={"metadata":{"schema_version":self.config.schema_version,"processing_version":self.config.processing_version,"rules_version":self.config.rules_version,"run_id":"RUN-"+now.replace(":","").replace("-","")[:15],"generated_at":now},
                "mentions":mentions,"conversations":conversation_list,"knowledge":knowledge,"insights":[],"statistics":stats,"errors":([] if self.sentiment_engine.backend == "pysentimiento" else [{"code":"SENTIMENT_FALLBACK","message":"pysentimiento no disponible; se utilizó fallback heurístico"}])}
        assert_valid_payload(result)
        return result
