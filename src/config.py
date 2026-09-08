from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

INPUT_DIR = BASE_DIR / "formularios"
OUTPUT_DIR = BASE_DIR / "output"

EXCEL_FILE = OUTPUT_DIR / "resultado.xlsx"

QUESTION_COORDINATES = {

    # =========================
    # Página 1
    # =========================
    1 : {
        "sexo": {
            "Masculino": (627, 765, 655, 797),
            "Feminino": (1010, 765, 1045, 800)
        },

        "cor": {
            "Branca": (497, 892, 530, 930),
            "Preta": (810, 892, 842, 930),
            "Amarela": (1082, 897, 1115, 927),
            "Parda": (1427, 892, 1460, 932),
            "Indígena": (1715, 895, 1745, 932)
        },

        "estado_civil": {
            "Solteiro": (497, 1022, 530, 1060),
            "Casado": (867, 1027, 895, 1060),
            "Divorciado": (1225, 1025, 1252, 1062),
            "Viúvo": (1665, 1025, 1697, 1060),
            "Separado": (497, 1095, 532, 1127),
            "União Estável": (870, 1095, 900, 1130)
        },
        "religiao": {
            "Católica": (717, 1157, 752, 1195),
            "Protestante": (1055, 1157, 1090, 1195),
            "Espírita": (1447, 1157, 1477, 1195),
            "Outra": (720, 1222, 752, 1260),
            "Sem Religião": (1455, 1225, 1485, 1260)
        },
        "trabalha": {
            "Sim": (740, 1290, 772, 1327),
            "Não": (1720, 1287, 1750, 1330)
        },

        "renda_mensal": {
            "Sim": (960, 1355, 990, 1392),
            "Não": (1982, 1357, 2017, 1395)
        },

        "tem_filhos": {
            "Sim": (775, 1422, 807, 1460),
            "Não": (1642, 1422, 1672, 1460)
        },

        "periodo_academico": {
            "Primeiro": (495, 1555, 510, 1592),
            "Segundo": (845, 1552, 872, 1595),
            "Terceiro": (1215, 1555, 1245, 1590),
            "Quarto": (1582, 1555, 1612, 1590),
            "Quinto": (1917, 1552, 1942, 1592)
        },

        "q10_ouviu_falar": {
            "Sim": (500, 1872, 532, 1910),
            "Não": (802, 1872, 830, 1912)
        },

        "q11_definicao": {
            "Apenas agressão física durante o parto": (500, 2002, 530, 2040),
            "Qualquer ato de desrespeito, abuso ou negligência durante o cuidado obstétrico": (496, 2070, 530, 2110),
            "Apenas erro médico": (502, 2202, 528, 2242),
            "Não sei": (500, 2270, 528, 2306)
        },

        "q12": {
            "procedimento_sem_consentimento": {
                "Sim": (498, 2468, 528, 2506),
                "Não": (896, 2466, 924, 2506),
                "Não sei": (1106, 2470, 1134, 2508)
            },

            "gritar_humilhar": {
                "Sim": (500, 2596, 530, 2636),
                "Não": (894, 2600, 924, 2638),
                "Não sei": (1106, 2598, 1134, 2638)
            },

            "episiotomia_rotina": {
                "Sim": (500, 2732, 530, 2770),
                "Não": (894, 2732, 926, 2770),
                "Não sei": (1104, 2730, 1132, 2770)
            },

            "impedir_acompanhante": {
                "Sim": (502, 2862, 528, 2904),
                "Não": (896, 2860, 926, 2904),
                "Não sei": (1104, 2860, 1132, 2900)
            },

            "negar_alivio_dor": {
                "Sim": (500, 2996, 532, 3036),
                "Não": (896, 2998, 922, 3038),
                "Não sei": (1102, 2996, 1134, 3036)
            },

            "comentarios_ofensivos": {
                "Sim": (500, 3126, 530, 3172),
                "Não": (898, 3126, 924, 3172),
                "Não sei": (1104, 3128, 1134, 3170)
            }
        }
    },

    # =========================
    # Página 2
    # =========================
    2 : {
        "q12_ocitocina_sem_explicacao": {
            "Sim": (502, 378, 528, 418),
            "Não": (898, 380, 926, 418),
            "Não sei": (1106, 378, 1134, 418)
        },
        
        "q13_autoavaliacao": {
            "Muito bom": (500, 510, 530, 548),
            "Bom": (500, 574, 530, 616),
            "Regular": (500, 640, 530, 684),
            "Ruim": (498, 708, 528, 748),
            "Muito ruim": (500, 776, 530, 814)
        }
    }
}


TEXT_FIELDS = {
    "questionario_numero": None,
    "idade": None,
    "religiao_outra": None,
    "ocupacao": None,
    "renda_valor": None,
    "quantidade_filhos": None,
    "data_coleta": None,
}