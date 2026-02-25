"""
============================================================
 Script: video_slicer.py
 Autor: Leandro
 Descrição:
   - Faz slices de um vídeo por intervalos nomeados
   - Aceita MM:SS ou HH:MM:SS
   - Apenas os mapeados são mantidos
   - Não mapeados são excluídos
============================================================
"""

import os
import subprocess
import sys

# ============================================================
# CONFIGURAÇÃO INLINE
# ============================================================

USE_INTERNAL_CONFIG = True

VIDEO_FILE = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Base\Vídeos baixados\Tyrese Gibson With T.D. Jakes\Tyrese_TDJakes.mp4"

GLOBAL_VIDEO_NAME = "Tyrese"

# 🔹 NOVA FLAG
# False → {nome_do_arquivo}_slicedFiles
# True  → 00slicedFiles (pasta compartilhada)
USE_SHARED_00_SLICED_FOLDER = False

SEGMENTS = [
{
"start": "00:00",
"end": "01:24",
"name": "01_IntroductionAndAccolades"
},
{
"start": "01:25",
"end": "02:37",
"name": "02_RecreatingYourself"
},
{
"start": "02:38",
"end": "04:05",
"name": "03_ConceptOfBlindFaith"
},
{
"start": "04:06",
"end": "05:15",
"name": "04_ConnectingPastAndPresent"
},
{
"start": "05:16",
"end": "06:15",
"name": "05_SurvivalIdentities"
},
{
"start": "06:16",
"end": "07:55",
"name": "06_TheBlackOctopusMetaphor"
},
{
"start": "07:56",
"end": "09:36",
"name": "07_IndividualIdentityCrisis"
},
{
"start": "09:37",
"end": "10:49",
"name": "08_HealthySelfishness"
},
{
"start": "10:50",
"end": "12:41",
"name": "09_ParentalBlueprintsAndGrief"
},
{
"start": "12:42",
"end": "14:21",
"name": "10_ForgivenessAndProtection"
},
{
"start": "14:22",
"end": "15:53",
"name": "11_DistortedViewsOfLove"
},
{
"start": "15:54",
"end": "17:30",
"name": "12_TrappedByFirstImpressions"
},
{
"start": "17:31",
"end": "19:12",
"name": "13_TheOrphanRealization"
},
{
"start": "19:13",
"end": "20:40",
"name": "14_HumorInTragedy"
},
{
"start": "20:41",
"end": "21:25",
"name": "15_TherapeuticInternalDialogue"
},
{
"start": "21:26",
"end": "22:43",
"name": "16_SurvivorsRemorseAndImpact"
},
{
"start": "22:44",
"end": "24:15",
"name": "17_TransparencyInSuccess"
},
{
"start": "24:16",
"end": "25:57",
"name": "18_TreasuresInDarkness"
},
{
"start": "25:58",
"end": "27:50",
"name": "19_SurrogateParentsAndRegard"
},
{
"start": "27:51",
"end": "29:13",
"name": "20_LeatherAndLacePartnership"
},
{
"start": "29:14",
"end": "30:42",
"name": "21_MixingBaggageAndTrauma"
},
{
"start": "30:43",
"end": "32:16",
"name": "22_SpiritualKnowingInRelationships"
},
{
"start": "32:17",
"end": "33:33",
"name": "23_BreakingTheHellCycle"
},
{
"start": "33:34",
"end": "34:47",
"name": "24_TheLanguageOfTherapy"
},
{
"start": "34:48",
"end": "36:10",
"name": "25_MutualHonorAndAttention"
},
{
"start": "36:11",
"end": "37:51",
"name": "26_CreativeIdealismVsSteadiness"
},
{
"start": "37:52",
"end": "39:33",
"name": "27_AppreciationForTransparency"
},
{
"start": "39:34",
"end": "41:15",
"name": "28_MaterialismVsLegacy"
},
{
"start": "41:16",
"end": "42:58",
"name": "29_MuchWithLittle"
},
{
"start": "42:59",
"end": "44:08",
"name": "30_AuthenticSelfPerception"
},
{
"start": "44:09",
"end": "45:44",
"name": "31_ProtectingChildrenDuringDivorce"
},
{
"start": "45:45",
"end": "47:30",
"name": "32_DaughtersChangePerspective"
},
{
"start": "47:31",
"end": "49:18",
"name": "33_LegalFinancialTrauma"
},
{
"start": "49:19",
"end": "50:50",
"name": "34_ComfortInMisunderstanding"
},
{
"start": "50:51",
"end": "52:27",
"name": "35_IntentionalSocialCircles"
},
{
"start": "52:28",
"end": "54:13",
"name": "36_AssignmentOverLife"
},
{
"start": "54:14",
"end": "56:08",
"name": "37_TraumaBondingAndBaggage"
},
{
"start": "56:09",
"end": "57:41",
"name": "38_MarryingTheScaffolding"
},
{
"start": "57:42",
"end": "59:43",
"name": "39_SeasonsAndChecklists"
},
{
"start": "59:44",
"end": "61:30",
"name": "40_LegacyOfTeddyPendergrass"
},
{
"start": "61:31",
"end": "63:00",
"name": "41_DeteriorationAndPerspective"
},
{
"start": "63:01",
"end": "64:51",
"name": "42_SocialCircleInfluence"
},
{
"start": "64:52",
"end": "66:13",
"name": "43_MentalHealthFragility"
},
{
"start": "66:14",
"end": "67:54",
"name": "44_TheSlingshotAnalogy"
},
{
"start": "67:55",
"end": "69:30",
"name": "45_DefiningSuccessAsImpact"
},
{
"start": "69:31",
"end": "71:01",
"name": "46_PrisonReformAndTrades"
},
{
"start": "71:02",
"end": "73:43",
"name": "47_ClosingBlessingAndConclusion"
}
]

FFMPEG_BIN = "ffmpeg"
FFPROBE_BIN = "ffprobe"

# ============================================================
# HELPERS
# ============================================================

def parse_time_to_seconds(value: str) -> int:
    parts = value.split(":")
    if len(parts) == 2:
        m, s = parts
        return int(m) * 60 + int(s)
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + int(s)
    raise ValueError(f"Formato inválido: {value}")


def get_video_duration(video_file: str) -> float:
    cmd = [
        FFPROBE_BIN,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_file
    ]
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True
    )
    return float(result.stdout.strip())


def run_ffmpeg(input_video: str, start: float, duration: float, output_file: str):
    cmd = [
        FFMPEG_BIN,
        "-y",
        "-ss", str(start),
        "-i", input_video,
        "-t", str(duration),
        "-c", "copy",
        output_file
    ]
    subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        check=True
    )

# ============================================================
# MAIN
# ============================================================

def main():
    if not USE_INTERNAL_CONFIG:
        print("Este script está configurado apenas para uso inline.")
        sys.exit(1)

    video_file = os.path.abspath(VIDEO_FILE)

    if not os.path.isfile(video_file):
        raise FileNotFoundError(f"Vídeo não encontrado: {video_file}")

    video_duration = get_video_duration(video_file)

    base_dir = os.path.dirname(video_file)
    base_name = os.path.splitext(os.path.basename(video_file))[0]

    # ========================================================
    # REGRA DA PASTA (ATUALIZADA)
    # ========================================================

    if USE_SHARED_00_SLICED_FOLDER:
        # Gera diretamente no próprio diretório do vídeo
        output_dir = base_dir
    else:
        # Gera na pasta {nome_do_arquivo}_slicedFiles
        output_dir = os.path.join(base_dir, f"{base_name}_slicedFiles")
        os.makedirs(output_dir, exist_ok=True)

    # ========================================================

    segments_seconds = [
        (
            parse_time_to_seconds(s["start"]),
            parse_time_to_seconds(s["end"]),
            s["name"]
        )
        for s in SEGMENTS
    ]

    segments_seconds.sort(key=lambda x: x[0])

    intervals = []
    cursor = 0

    for start, end, name in segments_seconds:
        if start > cursor:
            intervals.append((cursor, start, "nao_mapeado"))

        intervals.append((start, end, name))
        cursor = end

    if cursor < video_duration:
        intervals.append((cursor, video_duration, "nao_mapeado"))

    print("\n==================================================")
    print(" VIDEO SLICER (MAPPED ONLY)")
    print("==================================================")
    print(f"Arquivo origem.: {video_file}")
    print(f"Duração........: {video_duration:.2f}s")
    print(f"Pasta destino..: {output_dir}")
    print("==================================================\n")

    for i, (start, end, label) in enumerate(intervals, 1):
        output_name = (
            f"{GLOBAL_VIDEO_NAME}_{label}_"
            f"{int(start//60):02d}m{int(start%60):02d}s"
            f"_to_{int(end//60):02d}m{int(end%60):02d}s.mp4"
        )

        temp_output_path = os.path.join(base_dir, output_name)

        print(f"[{i}] Gerando: {output_name}")
        run_ffmpeg(video_file, start, end - start, temp_output_path)

        if label != "nao_mapeado":
            final_path = os.path.join(output_dir, output_name)
            os.replace(temp_output_path, final_path)
            print("    ✔ Movido para pasta de slices")
        else:
            os.remove(temp_output_path)
            print("    ✖ Não mapeado removido")

    print("\nProcesso finalizado com sucesso.")
    print("Apenas os trechos mapeados foram mantidos.")


if __name__ == "__main__":
    main()
