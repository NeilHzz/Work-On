from pathlib import Path


FILES = (
    "Gallus_G80966KZ.pdb",
    "Anas_G20030CU.pdb",
    "Columba_NeuAc1_GS00061.pdb",
)


def first_model_text(source: Path) -> str:
    lines: list[str] = []
    in_first_model = False
    for line in source.read_text(encoding="utf-8").splitlines(keepends=True):
        if line.startswith("MODEL"):
            if in_first_model:
                break
            in_first_model = True
        if in_first_model:
            lines.append(line)
            if line.startswith("ENDMDL"):
                break
    return "".join(lines) + "END\n"


output = Path("PDB_first_model")
output.mkdir(exist_ok=True)
for filename in FILES:
    source = Path("PDB") / filename
    (output / filename).write_text(first_model_text(source), encoding="utf-8")
