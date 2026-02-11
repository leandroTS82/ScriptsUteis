import os
import sys

PDF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Handouts", "pdf")


def list_pdfs():
    if not os.path.exists(PDF_DIR):
        print("Nenhuma pasta de PDFs encontrada.")
        return []

    files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]
    files.sort(reverse=True)
    return files


def open_pdf(path):
    if sys.platform.startswith("win"):
        os.startfile(path)
    elif sys.platform.startswith("darwin"):
        os.system(f"open \"{path}\"")
    else:
        os.system(f"xdg-open \"{path}\"")


def main():
    pdfs = list_pdfs()

    if not pdfs:
        print("Nenhum PDF encontrado.")
        input("\nPressione ENTER...")
        return

    print("\n══════════════════════════════════════")
    print("           PDFs Disponíveis")
    print("══════════════════════════════════════\n")

    for i, pdf in enumerate(pdfs, 1):
        print(f"{i} - {pdf}")

    choice = input("\nDigite o número do PDF para abrir (ou S para sair): ").strip().lower()

    if choice == "s":
        return

    if not choice.isdigit():
        print("Opção inválida.")
        input("\nPressione ENTER...")
        return

    index = int(choice) - 1

    if 0 <= index < len(pdfs):
        selected = os.path.join(PDF_DIR, pdfs[index])
        print("Abrindo:", pdfs[index])
        open_pdf(selected)
    else:
        print("Número inválido.")

    input("\nPressione ENTER para voltar ao menu...")


if __name__ == "__main__":
    main()
