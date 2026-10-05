from manual_ingest import parse_manual
from pipeline.orchestrator import Pipeline, PipelineConfig


def test_whatsapp_export_parser():
    txt='01/10/2026, 10:30 - Ana: Hola, necesito ayuda\n01/10/2026, 10:31 - Luis: Claro, te apoyo.'
    rows=parse_manual('chat.txt',txt,'whatsapp')
    assert len(rows)==2
    assert rows[0]['speaker']=='Ana'
    assert rows[0]['texto_original'].startswith('Hola')


def test_call_transcript_with_translation():
    rows=parse_manual('llamada.txt','Agente: The delivery was late.','call_transcript')
    rows[0]['texto_traducido']='La entrega fue tardía.'
    rows[0]['idioma_origen']='en'
    result=Pipeline(PipelineConfig()).run(rows)
    m=result['mentions'][0]
    assert m['texto_original']=='Agente: The delivery was late.'
    assert m['texto_traducido']=='La entrega fue tardía.'
    assert m['idioma_origen']=='en'
    assert m['idioma_analisis']=='es'
