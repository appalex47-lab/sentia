import argparse, json
from pathlib import Path
from .pipeline.orchestrator import Pipeline, PipelineConfig
from .pipeline.validation import assert_valid_payload

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",required=True)
    parser.add_argument("--output",default="data/datos_procesados.json")
    args=parser.parse_args()
    rows=json.loads(Path(args.input).read_text(encoding="utf-8"))
    if isinstance(rows,dict): rows=rows.get("mentions",[])
    result=Pipeline(PipelineConfig()).run(rows)
    assert_valid_payload(result)
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True)
    tmp=out.with_suffix(".tmp")
    tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    tmp.replace(out)
    print(f"Exportado: {out} ({len(result['mentions'])} menciones)")

if __name__=="__main__":
    main()
