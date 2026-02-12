import os
import sys
import subprocess
import importlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==========================================================
# 🎨 ANSI COLORS
# ==========================================================

RESET = "\033[0m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"

# ==========================================================
# 📦 DEPENDÊNCIAS NECESSÁRIAS DO FRAMEWORK
# ==========================================================

REQUIRED_PACKAGES = [
    "requests",
    "reportlab"
]

# ==========================================================
# 🧠 DEPENDENCY SCANNER + INSTALLER
# ==========================================================

def check_and_install_dependencies():
    missing = []

    print(f"{CYAN}🔎 Verificando dependências...{RESET}")

    for package in REQUIRED_PACKAGES:
        try:
            importlib.import_module(package)
        except ImportError:
            missing.append(package)

    if not missing:
        print(f"{GREEN}✅ Ambiente pronto para uso!{RESET}\n")
        return

    print(f"\n{YELLOW}⚠️ Dependências faltando:{RESET}")
    for pkg in missing:
        print(f"{RED} - {pkg}{RESET}")

    print(f"\n{CYAN}📦 Instalando automaticamente...{RESET}\n")

    for pkg in missing:
        subprocess.run([sys.executable, "-m", "pip", "install", pkg])

    print(f"\n{GREEN}🎉 Dependências instaladas com sucesso!{RESET}\n")
    input("Pressione ENTER para continuar...")

# ==========================================================
# 🚀 EXECUTOR DE SCRIPT
# ==========================================================

def run_script(script_name: str):
    script_path = os.path.join(BASE_DIR, script_name)

    if not os.path.exists(script_path):
        print(f"{RED}❌ Arquivo não encontrado: {script_name}{RESET}")
        input("\nPressione ENTER...")
        return

    # Limpa tela antes de executar módulo
    os.system("cls" if os.name == "nt" else "clear")

    subprocess.run([sys.executable, script_path])

    print(f"\n{MAGENTA}🔁 Retornando ao menu principal...{RESET}")
    input("Pressione ENTER para continuar...")

# ==========================================================
# 🎛 MENU VISUAL
# ==========================================================

def render_menu():
    os.system("cls" if os.name == "nt" else "clear")

    print(f"{CYAN}{BOLD}")
    print("═══════════════════════════════════════════")
    print("      🌍 English Knowledge Framework 🚀")
    print("═══════════════════════════════════════════")
    print(f"{RESET}")

    print(f"{GREEN}1️⃣  Tradução inteligente{RESET}")
    print(f"{GREEN}2️⃣  Tradução com contexto (acumulativo / narrativo / canção){RESET}")
    print(f"{GREEN}3️⃣  Tradução com gramática{RESET}")
    print(f"{GREEN}4️⃣  📄 Gerador de PDF manual{RESET}")
    print(f"{GREEN}5️⃣  🎮 GAME - MyAnki Trainer{RESET}")
    print(f"{GREEN}6️⃣  📚 Visualizar PDFs{RESET}")
    print(f"{RED}0️⃣  🚪 Sair{RESET}")

    print("\nEscolha uma opção: ", end="")

# ==========================================================
# 🏁 MAIN LOOP
# ==========================================================

def main():
    check_and_install_dependencies()

    while True:
        render_menu()
        choice = input().strip().lower()

        if choice == "1":
            run_script("w.py")

        elif choice == "2":
            run_script("w_context.py")

        elif choice == "3":
            run_script("e.py")

        elif choice == "4":
            run_script("doc.py")

        elif choice == "5":
            run_script("MyAnki.py")

        elif choice == "6":
            run_script("view_pdfs.py")

        elif choice in ("0", "s"):
            os.system("cls" if os.name == "nt" else "clear")
            print(f"{MAGENTA}👋 Obrigado por usar o English Knowledge Framework!{RESET}\n")
            break

        else:
            print(f"{RED}❌ Opção inválida.{RESET}")
            input("Pressione ENTER...")

# ==========================================================

if __name__ == "__main__":
    main()
