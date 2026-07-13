import asyncio
import sqlite3
import aiohttp
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, CopyTextButton, BufferedInputFile
from aiogram.exceptions import TelegramBadRequest
import re
import json
import time
import logging
from collections import deque
import random
import phonenumbers
import pyotp
import csv
from io import StringIO

logging.basicConfig(level=logging.INFO)

# ==================== CONFIG ====================
TOKEN = "8865186253:AAHZy2bd44y0ntk4p8XEvU9IGw7o1ZuZqdk"
OTP_GROUP_LINK = "https://t.me/otpchannal1"

FASTX_BASE_URL = "https://2eee7.com/@Access/@Bot/2eee7/@public/"
FASTX_API_KEY = "MURAD_1A19846FEA646F45D8EE07B6"

# সঠিক API এন্ডপয়েন্ট (ডকুমেন্টেশন অনুযায়ী)
GETNUM_URL = f"{FASTX_BASE_URL}/@Access/@Bot/2eee7/@public/api/getnum"
LIVE_CONSOLE_URL = f"{FASTX_BASE_URL}/@Access/@Bot/api/live-console"
SUCCESS_OTP_URL = f"{FASTX_BASE_URL}/@Access/@Bot/2eee7/@public/api/success-otp-info"
LIVEACCESS_URL = f"{FASTX_BASE_URL}/@Access/@Bot/2eee7/@public/api/liveaccess"

bot = Bot(token=TOKEN)
dp = Dispatcher()

db = sqlite3.connect("otp_pro_panel.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("PRAGMA journal_mode=WAL;")
cursor.execute("PRAGMA synchronous=NORMAL;")
cursor.execute("PRAGMA temp_store=MEMORY;")
cursor.execute("PRAGMA mmap_size=3000000000;")
db.commit()

# ==================== DATABASE ====================
cursor.execute("CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0, username TEXT, fullname TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS services (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, range_val TEXT, country_code TEXT, flag TEXT)")
cursor.execute("INSERT OR IGNORE INTO config VALUES ('maintenance_mode', 'off')")
cursor.execute("CREATE TABLE IF NOT EXISTS used_numbers (user_id INTEGER, number_id TEXT, phone_number TEXT, service_id INTEGER, used_at TEXT, PRIMARY KEY (user_id, number_id))")
cursor.execute("CREATE TABLE IF NOT EXISTS admins (user_id TEXT PRIMARY KEY)")
cursor.execute("CREATE TABLE IF NOT EXISTS otp_success_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, phone_number TEXT, otp_code TEXT, timestamp TEXT)")
cursor.execute("INSERT OR IGNORE INTO admins VALUES ('6820798198')")
cursor.execute("INSERT OR IGNORE INTO admins VALUES ('7689218221')")
cursor.execute("CREATE TABLE IF NOT EXISTS manual_services (id INTEGER PRIMARY KEY AUTOINCREMENT, service_name TEXT, country_name TEXT, flag TEXT, give_amount INTEGER DEFAULT 1, otp_rate REAL DEFAULT 0.0, stock INTEGER DEFAULT 0, cooldown INTEGER DEFAULT 0)")
cursor.execute("CREATE TABLE IF NOT EXISTS manual_numbers (id INTEGER PRIMARY KEY AUTOINCREMENT, service_id INTEGER, number TEXT, FOREIGN KEY(service_id) REFERENCES manual_services(id))")

try:
    cursor.execute("ALTER TABLE users ADD COLUMN active_manual TEXT")
except:
    pass
try:
    cursor.execute("ALTER TABLE users ADD COLUMN manual_cooldowns TEXT")
except:
    pass
try:
    cursor.execute("ALTER TABLE manual_services ADD COLUMN cooldown INTEGER DEFAULT 0")
except:
    pass
try:
    cursor.execute("ALTER TABLE services ADD COLUMN is_hot INTEGER DEFAULT 0")
except:
    pass
try:
    cursor.execute("ALTER TABLE services ADD COLUMN success_count INTEGER DEFAULT 0")
except:
    pass
try:
    cursor.execute("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0")
except:
    pass
try:
    cursor.execute("ALTER TABLE services ADD COLUMN updated_at TEXT")
except:
    pass

cursor.execute("CREATE INDEX IF NOT EXISTS idx_services_name ON services(name)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_services_country ON services(country_code)")
db.commit()

# ================= CUSTOM EMOJIS =================
CUSTOM_EMOJIS = {
    "phone": "6204108584381322968",
    "lock": "5251203410396458957",
    "folder": "5282843764451195532",
    "chart": "5231200819986047254",
    "gear": "6267097569722111582",
    "wave": "5389064576333527180",
    "lightning": "5424972470023104089",
    "cat_laptop": "5285288477015949061",
    "planet": "6285048454255220485",
    "globe": "5447410659077661506",
    "channel": "5458603043203327669",
    "chat": "5443038326535759644",
    "shopping": "5229064374403998351",
    "facebook": "5389064576333527180",
    "whatsapp": "5233354831984353090",
    "instagram": "5364310996179503764",
    "fire": "5424972470023104089",
    "success": "5273806972871787310",
    "error": "5271934564699226262",
    "trophy": "5440539497383087970",
    "users": "6307777408300753473",
    "search": "5231012545799666522",
    "broadcast": "5424818078833715060",
    "add": "5397916757333654639",
    "delete": "5445267414562389170",
    "back": "5332348837405145999",
    "ban": "5240241223632954241",
    "maintenance": "5366231924597604153",
    "signal": "5424818078833715060",
    "store": "5416041192905265756",
    "next": "5416117059207572332",
    "waiting": "5386367538735104399",
    "skull": "6282728866972702273",
    "cat": "5285288477015949061",
    "star": "5438496463044752972",
    "diamond": "5427168083074628963",
    "crown": "5217822164362739968",
    "gift": "5309849913218071967",
    "package": "5348149223223211884",
    "money": "5388622778817589921",
    "bank": "6258153613860805124",
    "card": "5389078268689265131",
    "chart_up": "5364295555772074912",
    "chart_down": "5246762912428603768",
    "red_circle": "5411225014148014586",
    "green_circle": "5416081784641168838",
    "warning": "5447644880824181073",
    "question": "5436113877181941026",
    "info": "5334544901428229844",
    "link": "5271604874419647061",
    "refresh": "5375338737028841420",
    "top": "5415655814079723871",
    "new": "5382357040008021292",
    "pin": "5397782960512444700",
    "email": "5253742260054409879",
    "bell": "5458603043203327669",
    "flag_af": "5291937511591925566",
    "flag_ax": "5294077418917616055",
    "flag_al": "5294202819077756005",
    "flag_dz": "5294048127240655242",
    "flag_as": "5291994273879709721",
    "flag_ad": "5294215205763434181",
    "flag_ao": "5294516785482062829",
    "flag_ai": "5292186323342350940",
    "flag_ag": "5294005972136647964",
    "flag_ar": "5292208210495689627",
    "flag_am": "5291978717508164018",
    "flag_aw": "5294007002928798927",
    "flag_au": "5294444247779399477",
    "flag_at": "5291975174160145850",
    "flag_az": "5294323533428579078",
    "flag_bs": "5294031587321600012",
    "flag_bh": "5294108398516720753",
    "flag_bd": "5291824686097827834",
    "flag_bb": "5294526187165471742",
    "flag_by": "5294134426018536120",
    "flag_be": "5291774466043435275",
    "flag_bz": "5294171848068584842",
    "flag_bj": "5293984969746566866",
    "flag_bt": "5294121983498277263",
    "flag_bo": "5294201479047957700",
    "flag_bw": "5294026179957772585",
    "flag_br": "5291892229751723900",
    "flag_bn": "5292098293692650297",
    "flag_bg": "5294308947719640437",
    "flag_bf": "5294153164960848949",
    "flag_bi": "5294051631933967760",
    "flag_kh": "5294225191562400452",
    "flag_cm": "5291997306126626950",
    "flag_ca": "5292290347450259214",
    "flag_cv": "5292203503211535593",
    "flag_cf": "5294210571493724819",
    "flag_td": "5291780728105753403",
    "flag_cl": "5294231037012888049",
    "flag_cn": "5294068833277990704",
    "flag_co": "5294010206974397371",
    "flag_km": "5294351381996521508",
    "flag_cg": "5294035229453865597",
    "flag_ck": "5292098684534675100",
    "flag_cr": "5292063805105265554",
    "flag_ci": "5293991322003200135",
    "flag_hr": "5291999676948569127",
    "flag_cu": "5291963947115631526",
    "flag_cy": "5294062721539526918",
    "flag_cz": "5294242852467923382",
    "flag_dk": "5294531860817268837",
    "flag_dj": "5294127214768468283",
    "flag_dm": "5294485513825178032",
    "flag_do": "5294522197140857947",
    "flag_ec": "5292083733753517221",
    "flag_eg": "5293992082212409502",
    "flag_sv": "5294337307388695687",
    "flag_england": "5294410107084365278",
    "flag_gq": "5292170045416297012",
    "flag_er": "5291922054004625949",
    "flag_ee": "5291951143818123103",
    "flag_et": "5292245976143124155",
    "flag_eu": "5291992809295861098",
    "flag_gi": "5292055799286224027",
    "flag_gm": "5294399820637688352",
    "flag_gl": "5292014752283774878",
    "flag_fi": "5294049961191690629",
    "flag_fr": "5291817660529533837",
    "flag_ga": "5294321325815389139",
    "flag_ge": "5294349389131697267",
    "flag_de": "5292013274815028523",
    "flag_gh": "5294347396266873249",
    "flag_gr": "5291948395039054764",
    "flag_gw": "5294409819321550432",
    "flag_gt": "5294336633078831209",
    "flag_gn": "5291892096607739008",
    "flag_gy": "5292062692708736193",
    "flag_ht": "5292045130587462814",
    "flag_hn": "5291901034434682297",
    "flag_hk": "5292166459118606932",
    "flag_hu": "5294229581018975260",
    "flag_is": "5294354358408859664",
    "flag_in": "5291933173674957761",
    "flag_ir": "5294220170745630736",
    "flag_iq": "5294325010897327367",
    "flag_ie": "5294471971793293647",
    "flag_im": "5294318478252070646",
    "flag_il": "5294069056616289553",
    "flag_it": "5291826830284709120",
    "flag_jm": "5294505107465982830",
    "flag_jp": "5291799063321139445",
    "flag_je": "5291950280529697493",
    "flag_jo": "5291988613112814801",
    "flag_kz": "5294227175837290463",
    "flag_ke": "5292111852904416801",
    "flag_ki": "5294538934628405146",
    "flag_kp": "5294193812531333564",
    "flag_kr": "5294408281723262763",
    "flag_kw": "5292066437920218075",
    "flag_kg": "5292091954320922577",
    "flag_la": "5291981530711746037",
    "flag_lv": "5292236016113966127",
    "flag_lb": "5294193108156699621",
    "flag_ls": "5292040693886247604",
    "flag_lr": "5291793810576137439",
    "flag_ly": "5291858711826946840",
    "flag_li": "5292048742654957785",
    "flag_lt": "5294343084119708700",
    "flag_lu": "5294423709245787718",
    "flag_mk": "5294023611567332075",
    "flag_mg": "5291991568050312348",
    "flag_mw": "5294241881805312589",
    "flag_my": "5291858351049696702",
    "flag_mv": "5292004203844097218",
    "flag_ml": "5292086972158858331",
    "flag_mt": "5294532213004588353",
    "flag_mh": "5294180730060954484",
    "flag_mr": "5294429743674840973",
    "flag_mu": "5294127824653797277",
    "flag_mx": "5294535073452809778",
    "flag_fm": "5291838156113470124",
    "flag_md": "5294158486425325375",
    "flag_mc": "5294378161117614233",
    "flag_mn": "5294316532631883496",
    "flag_ma": "5292108962391414885",
    "flag_mz": "5294086708931874940",
    "flag_mm": "5294254478943569269",
    "flag_na": "5292021761670404922",
    "flag_nr": "5294463274484521342",
    "flag_np": "5294458756178924088",
    "flag_nl": "5291917797692042265",
    "flag_nz": "5294189019347833274",
    "flag_ni": "5294240825243358100",
    "flag_ne": "5291809418487290691",
    "flag_ng": "5294456308047563965",
    "flag_nu": "5294471336138134209",
    "flag_no": "5291761718580502030",
    "flag_om": "5291813666209946812",
    "flag_pk": "5291825606219029010",
    "flag_ps": "5294289826525238172",
    "flag_pa": "5291959935616178405",
    "flag_pg": "5291917995260533077",
    "flag_py": "5294525611639852679",
    "flag_ph": "5291798075478661634",
    "flag_pe": "5292099427564018941",
    "flag_pl": "5292190970496963836",
    "flag_pt": "5294436555492973610",
    "flag_pr": "5292121516580820347",
    "flag_qa": "5292166360334357676",
    "flag_ro": "5294107724206856227",
    "flag_ru": "5294335323113807278",
    "flag_rw": "5294191265615729158",
    "flag_sm": "5292147350809106831",
    "flag_st": "5292183188016222701",
    "flag_sa": "5294163983983463099",
    "flag_scotland": "5294434665707368018",
    "flag_sn": "5292087023698466689",
    "flag_rs": "5294458584380230360",
    "flag_sc": "5291891186074672309",
    "flag_sl": "5294494314213167952",
    "flag_sg": "5294451304410663668",
    "flag_sk": "5294538440707166931",
    "flag_si": "5294279359689938006",
    "flag_sb": "5294283890880433237",
    "flag_so": "5294058817414255960",
    "flag_za": "5294325281480266304",
    "flag_es": "5294513087515216901",
    "flag_lk": "5292102670264328257",
    "flag_sd": "5294177148058228060",
    "flag_sr": "5294396668131692138",
    "flag_sz": "5294312482477724867",
    "flag_se": "5291737091238026321",
    "flag_ch": "5291791748991835084",
    "flag_sy": "5294013428199869487",
    "flag_tw": "5294095745543069603",
    "flag_tj": "5294120269806328883",
    "flag_tz": "5292146096678658977",
    "flag_th": "5293994384314882755",
    "flag_tg": "5294097669688415562",
    "flag_to": "5294283689016973348",
    "flag_tt": "5294362935458548705",
    "flag_tn": "5294484680601521871",
    "flag_tr": "5293993400767367408",
    "flag_tm": "5294098958178603764",
    "flag_tc": "5294320866253884749",
    "flag_us": "5294244076533600593",
    "flag_ug": "5294192317882716626",
    "flag_ae": "5294314831824835370",
    "flag_gb": "5293993521026453119",
    "flag_ua": "5294263837678131580",
    "flag_vu": "5294448585696368047",
    "flag_uz": "5294217645304864345",
    "flag_uy": "5291928449210932974",
    "flag_ve": "5294476442854247878",
    "flag_vn": "5294235963340379688",
    "flag_vi": "5294228039125718124",
    "flag_wales": "5294139949346476093",
    "flag_ye": "5294058972033076492",
    "flag_zm": "5294100109229838880",
    "flag_zw": "5294422158762592930",
}

COUNTRY_PREFIXES = {
    "1": "US", "7": "RU", "20": "EG", "27": "ZA", "30": "GR", "31": "NL", "32": "BE", "33": "FR",
    "34": "ES", "36": "HU", "39": "IT", "40": "RO", "41": "CH", "43": "AT", "44": "GB", "45": "DK",
    "46": "SE", "47": "NO", "48": "PL", "49": "DE", "51": "PE", "52": "MX", "53": "CU", "54": "AR",
    "55": "BR", "56": "CL", "57": "CO", "58": "VE", "60": "MY", "61": "AU", "62": "ID", "63": "PH",
    "64": "NZ", "65": "SG", "66": "TH", "81": "JP", "82": "KR", "84": "VN", "86": "CN", "90": "TR",
    "91": "IN", "92": "PK", "93": "AF", "94": "LK", "95": "MM", "98": "IR", "212": "MA", "213": "DZ",
    "216": "TN", "218": "LY", "220": "GM", "221": "SN", "222": "MR", "223": "ML", "224": "GN",
    "225": "CI", "226": "BF", "227": "NE", "228": "TG", "229": "BJ", "230": "MU", "231": "LR",
    "232": "SL", "233": "GH", "234": "NG", "235": "TD", "236": "CF", "237": "CM", "238": "CV",
    "239": "ST", "240": "GQ", "241": "GA", "242": "CG", "243": "CD", "244": "AO", "245": "GW",
    "246": "IO", "247": "AC", "248": "SC", "249": "SD", "250": "RW", "251": "ET", "252": "SO",
    "253": "DJ", "254": "KE", "255": "TZ", "256": "UG", "257": "BI", "258": "MZ", "260": "ZM",
    "261": "MG", "262": "RE", "263": "ZW", "264": "NA", "265": "MW", "266": "LS", "267": "BW",
    "268": "SZ", "269": "KM", "290": "SH", "291": "ER", "297": "AW", "298": "FO", "299": "GL",
    "350": "GI", "351": "PT", "352": "LU", "353": "IE", "354": "IS", "355": "AL", "356": "MT",
    "357": "CY", "358": "FI", "359": "BG", "370": "LT", "371": "LV", "372": "EE", "373": "MD",
    "374": "AM", "375": "BY", "376": "AD", "377": "MC", "378": "SM", "379": "VA", "380": "UA",
    "381": "RS", "382": "ME", "383": "XK", "385": "HR", "386": "SI", "387": "BA", "389": "MK",
    "420": "CZ", "421": "SK", "423": "LI", "500": "FK", "501": "BZ", "502": "GT", "503": "SV",
    "504": "HN", "505": "NI", "506": "CR", "507": "PA", "508": "PM", "509": "HT", "590": "GP",
    "591": "BO", "592": "GY", "593": "EC", "594": "GF", "595": "PY", "596": "MQ", "597": "SR",
    "598": "UY", "599": "BQ", "670": "TL", "672": "NF", "673": "BN", "674": "NR", "675": "PG",
    "676": "TO", "677": "SB", "678": "VU", "679": "FJ", "680": "PW", "681": "WF", "682": "CK",
    "683": "NU", "685": "WS", "686": "KI", "687": "NC", "688": "TV", "689": "PF", "690": "TK",
    "691": "FM", "692": "MH", "850": "KP", "852": "HK", "853": "MO", "855": "KH", "856": "LA",
    "880": "BD", "886": "TW", "960": "MV", "961": "LB", "962": "JO", "963": "SY", "964": "IQ",
    "965": "KW", "966": "SA", "967": "YE", "968": "OM", "970": "PS", "971": "AE", "972": "IL",
    "973": "BH", "974": "QA", "975": "BT", "976": "MN", "977": "NP", "992": "TJ", "993": "TM",
    "994": "AZ", "995": "GE", "996": "KG", "998": "UZ"
}

COUNTRY_NAMES = {
    "AF": "Afghanistan", "AX": "Åland Islands", "AL": "Albania", "DZ": "Algeria", "AS": "American Samoa",
    "AD": "Andorra", "AO": "Angola", "AI": "Anguilla", "AG": "Antigua and Barbuda", "AR": "Argentina",
    "AM": "Armenia", "AW": "Aruba", "AU": "Australia", "AT": "Austria", "AZ": "Azerbaijan", "BS": "Bahamas",
    "BH": "Bahrain", "BD": "Bangladesh", "BB": "Barbados", "BY": "Belarus", "BE": "Belgium", "BZ": "Belize",
    "BJ": "Benin", "BT": "Bhutan", "BO": "Bolivia", "BA": "Bosnia and Herzegovina", "BW": "Botswana",
    "BR": "Brazil", "BN": "Brunei", "BG": "Bulgaria", "BF": "Burkina Faso", "BI": "Burundi", "KH": "Cambodia",
    "CM": "Cameroon", "CA": "Canada", "CV": "Cape Verde", "CF": "Central African Republic", "TD": "Chad",
    "CL": "Chile", "CN": "China", "CO": "Colombia", "KM": "Comoros", "CG": "Congo", "CK": "Cook Islands",
    "CR": "Costa Rica", "CI": "Côte d'Ivoire", "HR": "Croatia", "CU": "Cuba", "CY": "Cyprus", "CZ": "Czechia",
    "DK": "Denmark", "DJ": "Djibouti", "DM": "Dominica", "DO": "Dominican Republic", "EC": "Ecuador",
    "EG": "Egypt", "SV": "El Salvador", "GQ": "Equatorial Guinea", "ER": "Eritrea", "EE": "Estonia",
    "ET": "Ethiopia", "FK": "Falkland Islands", "FO": "Faroe Islands", "FJ": "Fiji", "FI": "Finland",
    "FR": "France", "GF": "French Guiana", "PF": "French Polynesia", "GA": "Gabon", "GM": "Gambia",
    "GE": "Georgia", "DE": "Germany", "GH": "Ghana", "GI": "Gibraltar", "GR": "Greece", "GL": "Greenland",
    "GD": "Grenada", "GP": "Guadeloupe", "GU": "Guam", "GT": "Guatemala", "GG": "Guernsey", "GN": "Guinea",
    "GW": "Guinea-Bissau", "GY": "Guyana", "HT": "Haiti", "HN": "Honduras", "HK": "Hong Kong", "HU": "Hungary",
    "IS": "Iceland", "IN": "India", "ID": "Indonesia", "IR": "Iran", "IQ": "Iraq", "IE": "Ireland",
    "IM": "Isle of Man", "IL": "Israel", "IT": "Italy", "JM": "Jamaica", "JP": "Japan", "JE": "Jersey",
    "JO": "Jordan", "KZ": "Kazakhstan", "KE": "Kenya", "KI": "Kiribati", "KP": "North Korea", "KR": "South Korea",
    "KW": "Kuwait", "KG": "Kyrgyzstan", "LA": "Laos", "LV": "Latvia", "LB": "Lebanon", "LS": "Lesotho",
    "LR": "Liberia", "LY": "Libya", "LI": "Liechtenstein", "LT": "Lithuania", "LU": "Luxembourg",
    "MO": "Macao", "MK": "North Macedonia", "MG": "Madagascar", "MW": "Malawi", "MY": "Malaysia",
    "MV": "Maldives", "ML": "Mali", "MT": "Malta", "MH": "Marshall Islands", "MQ": "Martinique",
    "MR": "Mauritania", "MU": "Mauritius", "YT": "Mayotte", "MX": "Mexico", "FM": "Micronesia",
    "MD": "Moldova", "MC": "Monaco", "MN": "Mongolia", "ME": "Montenegro", "MS": "Montserrat", "MA": "Morocco",
    "MZ": "Mozambique", "MM": "Myanmar", "NA": "Namibia", "NR": "Nauru", "NP": "Nepal", "NL": "Netherlands",
    "NC": "New Caledonia", "NZ": "New Zealand", "NI": "Nicaragua", "NE": "Niger", "NG": "Nigeria", "NU": "Niue",
    "NF": "Norfolk Island", "MP": "Northern Mariana Islands", "NO": "Norway", "OM": "Oman", "PK": "Pakistan",
    "PW": "Palau", "PS": "Palestine", "PA": "Panama", "PG": "Papua New Guinea", "PY": "Paraguay", "PE": "Peru",
    "PH": "Philippines", "PN": "Pitcairn", "PL": "Poland", "PT": "Portugal", "PR": "Puerto Rico", "QA": "Qatar",
    "RE": "Réunion", "RO": "Romania", "RU": "Russia", "RW": "Rwanda", "BL": "Saint Barthélemy", "SH": "Saint Helena",
    "KN": "Saint Kitts and Nevis", "LC": "Saint Lucia", "MF": "Saint Martin", "PM": "Saint Pierre and Miquelon",
    "VC": "Saint Vincent and the Grenadines", "WS": "Samoa", "SM": "San Marino", "ST": "Sao Tome and Principe",
    "SA": "Saudi Arabia", "SN": "Senegal", "RS": "Serbia", "SC": "Seychelles", "SL": "Sierra Leone", "SG": "Singapore",
    "SX": "Sint Maarten", "SK": "Slovakia", "SI": "Slovenia", "SB": "Solomon Islands", "SO": "Somalia",
    "ZA": "South Africa", "GS": "South Georgia", "SS": "South Sudan", "ES": "Spain", "LK": "Sri Lanka",
    "SD": "Sudan", "SR": "Suriname", "SJ": "Svalbard and Jan Mayen", "SZ": "Swaziland", "SE": "Sweden",
    "CH": "Switzerland", "SY": "Syria", "TW": "Taiwan", "TJ": "Tajikistan", "TZ": "Tanzania", "TH": "Thailand",
    "TL": "Timor-Leste", "TG": "Togo", "TK": "Tokelau", "TO": "Tonga", "TT": "Trinidad and Tobago", "TN": "Tunisia",
    "TR": "Turkey", "TM": "Turkmenistan", "TC": "Turks and Caicos Islands", "TV": "Tuvalu", "UG": "Uganda",
    "UA": "Ukraine", "AE": "United Arab Emirates", "GB": "United Kingdom", "US": "United States", "UY": "Uruguay",
    "UZ": "Uzbekistan", "VU": "Vanuatu", "VA": "Vatican City", "VE": "Venezuela", "VN": "Vietnam",
    "VG": "British Virgin Islands", "VI": "U.S. Virgin Islands", "WF": "Wallis and Futuna", "EH": "Western Sahara",
    "YE": "Yemen", "ZM": "Zambia", "ZW": "Zimbabwe"
}

def get_country_name(country_code: str) -> str:
    if not country_code or len(country_code) != 2:
        return "Unknown"
    return COUNTRY_NAMES.get(country_code.upper(), country_code.upper())

def get_custom_flag_emoji(country_code: str) -> str:
    if not country_code or len(country_code) != 2:
        return "🌍"
    key = f"flag_{country_code.lower()}"
    if key in CUSTOM_EMOJIS:
        return f'<tg-emoji emoji-id="{CUSTOM_EMOJIS[key]}">🏳️</tg-emoji>'
    return "🌍"

def get_custom_flag_icon_id(country_code: str) -> str:
    if not country_code or len(country_code) != 2:
        return CUSTOM_EMOJIS.get("globe", "5447410659077661506")
    key = f"flag_{country_code.lower()}"
    if key in CUSTOM_EMOJIS:
        return CUSTOM_EMOJIS[key]
    return CUSTOM_EMOJIS.get("globe", "5447410659077661506")

def get_country_from_phone(phone: str) -> tuple:
    digits = ''.join(filter(str.isdigit, str(phone)))
    if not digits:
        return "", ""
    for length in range(min(6, len(digits)), 0, -1):
        prefix = digits[:length]
        if prefix in COUNTRY_PREFIXES:
            code = COUNTRY_PREFIXES[prefix]
            flag_emoji = get_custom_flag_emoji(code)
            return code, flag_emoji
    return "", ""

def get_country_info(phone: str) -> tuple:
    digits = ''.join(filter(str.isdigit, str(phone)))
    for length in range(min(6, len(digits)), 0, -1):
        prefix = digits[:length]
        if prefix in COUNTRY_PREFIXES:
            code = COUNTRY_PREFIXES[prefix]
            flag = "".join(chr(ord(c) + 127397) for c in code)
            return flag, code
    test_num = str(phone).upper().replace('X', '0').replace('x', '0')
    try:
        if not test_num.startswith('+'):
            test_num = '+' + test_num
        parsed = phonenumbers.parse(test_num, None)
        region = phonenumbers.region_code_for_number(parsed)
        if region:
            flag = "".join(chr(ord(c) + 127397) for c in region)
            return flag, region
    except:
        pass
    return "🌍", "GLOBAL"

async def safe_send_message(target, text, reply_markup=None, parse_mode="HTML"):
    try:
        if isinstance(target, types.Message):
            return await target.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
        elif hasattr(target, "answer"):
            return await target.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
        else:
            return await target.message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except TelegramBadRequest:
        stripped = re.sub(r'<tg-emoji emoji-id="\d+">(.*?)</tg-emoji>', r'\1', text)
        stripped = re.sub(r'<[^>]+>', '', stripped)
        if isinstance(target, types.Message):
            return await target.answer(stripped, reply_markup=reply_markup)
        elif hasattr(target, "answer"):
            return await target.answer(stripped, reply_markup=reply_markup)
        else:
            return await target.message.answer(stripped, reply_markup=reply_markup)

async def safe_edit_message(target_message, text, reply_markup=None, parse_mode="HTML"):
    try:
        return await target_message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except TelegramBadRequest:
        stripped = re.sub(r'<tg-emoji emoji-id="\d+">(.*?)</tg-emoji>', r'\1', text)
        stripped = re.sub(r'<[^>]+>', '', stripped)
        return await target_message.edit_text(stripped, reply_markup=reply_markup)

@dp.errors()
async def global_error_handler(update, exception):
    logging.error(f"Unhandled exception: {exception}", exc_info=True)
    if update and hasattr(update, "message") and update.message:
        try:
            await update.message.answer("⚠️ একটি ত্রুটি ঘটেছে, দয়া করে আবার চেষ্টা করুন।")
        except:
            pass
    return True

def format_number_with_plus(phone: str) -> str:
    if phone.startswith('+'):
        return phone
    return f"+{phone}"

def is_admin(user_id: int) -> bool:
    cursor.execute("SELECT 1 FROM admins WHERE user_id=?", (str(user_id),))
    return cursor.fetchone() is not None

def is_banned(user_id: int) -> bool:
    row = cursor.execute("SELECT is_banned FROM users WHERE id=?", (user_id,)).fetchone()
    return row and row[0] == 1

def is_maintenance_mode() -> bool:
    row = cursor.execute("SELECT value FROM config WHERE key='maintenance_mode'").fetchone()
    return row and row[0] == "on"

async def check_maintenance(user_id: int, message: types.Message = None, callback: types.CallbackQuery = None):
    if is_banned(user_id):
        text = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["ban"]}">🚫</tg-emoji> <b>You are banned from using this bot.</b> Contact Admin.'
        if callback:
            await callback.answer("You are banned.", show_alert=True)
            await safe_edit_message(callback.message, text, parse_mode="HTML")
        elif message:
            await safe_send_message(message, text, parse_mode="HTML")
        return True
    if is_maintenance_mode() and not is_admin(user_id):
        text = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["maintenance"]}">🔧</tg-emoji> <b>Bot is under maintenance.</b> Please try again later.'
        if callback:
            await callback.answer("Maintenance mode is ON", show_alert=True)
            await safe_edit_message(callback.message, text, parse_mode="HTML")
        elif message:
            await safe_send_message(message, text, parse_mode="HTML")
        return True
    return False

user_processed_otps = deque(maxlen=5000)
active_manual_pollers = {}

def extract_otp(message):
    if not message:
        return None
    message_str = str(message).strip().upper()
    if message_str in ["0", "00", "000", "0000", "000000", "NULL", "NONE", "WAITING", "PENDING", ""]:
        return None
    wa_match = re.search(r'(?i)(?:WHATSAPP|WA|CODE).*?(\d{3})[- ]?(\d{3})', message_str)
    if wa_match:
        return wa_match.group(1) + wa_match.group(2)
    ast_match = re.search(r'\*{4,8}', message_str)
    if ast_match:
        return ''.join(random.choices('0123456789', k=len(ast_match.group(0))))
    split_match = re.search(r'(?<!\d)(\d{3,4})[\s-](\d{3,4})(?!\d)', message_str)
    if split_match:
        return split_match.group(1) + split_match.group(2)
    stand_alone_match = re.findall(r'(?<!\d)(\d{4,8})(?!\d)', message_str)
    if stand_alone_match:
        for match in stand_alone_match:
            if not re.match(r'^0+$', match):
                return match
    numbers = re.findall(r'\d{4,8}', message_str.replace(" ", "").replace("-", ""))
    if numbers:
        for match in numbers:
            if not re.match(r'^0+$', match):
                return match[:8]
    return None

class AdminStates(StatesGroup):
    waiting_service_name = State()
    waiting_range_val = State()
    waiting_country_code = State()
    waiting_broadcast = State()
    waiting_add_admin = State()
    waiting_remove_admin = State()
    waiting_manual_file = State()
    waiting_manual_svc_name = State()
    waiting_manual_country = State()
    waiting_manual_give_amount = State()
    waiting_manual_cooldown = State()
    waiting_search_user = State()
    waiting_otp_channel = State()
    waiting_ban_user = State()
    waiting_unban_user = State()

class UserStates(StatesGroup):
    waiting_for_range = State()
    waiting_for_2fa = State()

# ==================== পেন্ডিং OTP ট্র্যাকার ====================
pending_otps = {}
last_console_id = 0

# ==================== সঠিক GETNUM ফাংশন (POST /api/getnum) ====================
async def fastx_get_number(range_val: str) -> tuple[str, str] | tuple[None, None]:
    """রেঞ্জ থেকে নাম্বার নেয় – ডকুমেন্টেশন অনুযায়ী POST /api/getnum"""
    if not FASTX_API_KEY:
        return None, None
    async with aiohttp.ClientSession() as session:
        headers = {
            "X-API-Key": FASTX_API_KEY,
            "Content-Type": "application/json"
        }
        # রেঞ্জের শেষে XXX না থাকলে যোগ করি
        if not range_val.endswith("XXX"):
            range_val = range_val + "XXX"
        payload = {"range": range_val}
        try:
            async with session.post(GETNUM_URL, json=payload, headers=headers, timeout=15) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("meta", {}).get("code") == 200 and data.get("data"):
                        full_number = data["data"].get("full_number")
                        if full_number:
                            return full_number, None
                return None, None
        except Exception as e:
            logging.error(f"FastX getnum error: {e}")
            return None, None

# ==================== লাইভ কনসোল পোলার ====================
async def live_console_poller():
    global last_console_id
    headers = {"X-API-Key": FASTX_API_KEY, "Accept": "application/json"}
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                url = f"{LIVE_CONSOLE_URL}?since={last_console_id}&limit=55"
                async with session.get(url, headers=headers, timeout=15) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("meta", {}).get("code") == 200:
                            otps = data.get("data", {}).get("otps", [])
                            new_max = data.get("data", {}).get("max_id", 0)
                            if new_max > last_console_id:
                                last_console_id = new_max
                            for otp in reversed(otps):
                                phone_full = otp.get("number", "")
                                if not phone_full:
                                    continue
                                phone_clean = re.sub(r'\D', '', phone_full)
                                if not phone_clean:
                                    continue
                                if phone_clean in pending_otps:
                                    pending = pending_otps[phone_clean]
                                    user_id = pending["user_id"]
                                    range_val = pending.get("range_val")
                                    service_name = pending.get("service_name", "UNKNOWN")
                                    platform = otp.get("platform", "")
                                    if platform:
                                        service_name = platform
                                    otp_code = otp.get("otp", "")
                                    if otp_code:
                                        await process_otp_reward(user_id, phone_clean, otp_code, range_val=range_val, service_name=service_name)
                                        del pending_otps[phone_clean]
                    else:
                        logging.warning(f"Live console status: {resp.status}")
            except Exception as e:
                logging.error(f"Live console poller error: {e}")
            await asyncio.sleep(3)

# ==================== সাকসেস OTP চেকার ====================
async def success_otp_checker():
    headers = {"X-API-Key": FASTX_API_KEY, "Accept": "application/json"}
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(SUCCESS_OTP_URL, headers=headers, timeout=15) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("meta", {}).get("code") == 200:
                            otps = data.get("data", {}).get("otps", [])
                            for otp in otps:
                                phone_full = otp.get("number", "")
                                if not phone_full:
                                    continue
                                phone_clean = re.sub(r'\D', '', phone_full)
                                if phone_clean in pending_otps:
                                    pending = pending_otps[phone_clean]
                                    user_id = pending["user_id"]
                                    range_val = pending.get("range_val")
                                    service_name = pending.get("service_name", "UNKNOWN")
                                    if otp.get("platform"):
                                        service_name = otp["platform"]
                                    otp_code = otp.get("otp", "")
                                    if otp_code:
                                        await process_otp_reward(user_id, phone_clean, otp_code, range_val=range_val, service_name=service_name)
                                        del pending_otps[phone_clean]
            except Exception as e:
                logging.error(f"Success OTP checker error: {e}")
            await asyncio.sleep(10)

# ==================== পেন্ডিং এক্সপায়ার ====================
async def pending_expiry():
    while True:
        now = time.time()
        expired = []
        for phone, data in pending_otps.items():
            if now - data.get("start_time", 0) > 1200:
                expired.append(phone)
        for phone in expired:
            del pending_otps[phone]
        await asyncio.sleep(60)

# ==================== ফাস্টএক্স লাইভ অ্যাক্সেস আপডেটার (শুধু হাই-ট্রাফিক) ====================
async def fastx_liveaccess_updater():
    ALLOWED_CATEGORIES = {"FACEBOOK", "WHATSAPP", "INSTAGRAM", "NEW FB"}
    while True:
        if FASTX_API_KEY:
            headers = {"X-API-Key": FASTX_API_KEY, "Accept": "application/json"}
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(LIVEACCESS_URL, headers=headers, timeout=15) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            services_list = data.get("services", [])
                            now_time = datetime.now().isoformat()
                            local_db = sqlite3.connect("otp_pro_panel.db", check_same_thread=False)
                            local_cur = local_db.cursor()
                            local_cur.execute("DELETE FROM services")
                            inserted_count = 0
                            country_count = {}
                            for svc in services_list:
                                sid = svc.get("sid", "").upper()
                                if sid == "WHATSAPP":
                                    sid = "INSTAGRAM"
                                if sid not in ALLOWED_CATEGORIES:
                                    continue
                                ranges = svc.get("ranges", [])
                                for rng in ranges:
                                    clean_rng = rng.strip()
                                    flag, c_code = get_country_info(clean_rng)
                                    if c_code not in country_count:
                                        country_count[c_code] = 0
                                    if country_count[c_code] >= 5:
                                        continue
                                    country_count[c_code] += 1
                                    local_cur.execute(
                                        "INSERT INTO services (name, range_val, country_code, flag, is_hot, updated_at) VALUES (?,?,?,?,?,?)",
                                        (sid, clean_rng, c_code, flag, 1, now_time)
                                    )
                                    inserted_count += 1
                            local_db.commit()
                            local_db.close()
                            logging.info(f"FastX updater: {inserted_count} ranges inserted (max 5 per country).")
                        else:
                            logging.error(f"FastX liveaccess status: {resp.status}")
                except Exception as e:
                    logging.error(f"FastX liveaccess updater error: {e}")
        await asyncio.sleep(60)

# ==================== OTP রিওয়ার্ড প্রসেসর ====================
async def process_otp_reward(user_id: int, phone: str, otp: str, rate_override=None, range_val: str = None, service_name: str = "New FB"):
    unique_key = f"{phone}_{otp}"
    if unique_key in user_processed_otps:
        return
    user_processed_otps.append(unique_key)
    try:
        cursor.execute("INSERT INTO otp_success_logs (user_id, phone_number, otp_code, timestamp) VALUES (?, ?, ?, ?)", 
                      (user_id, phone, otp, datetime.now().isoformat()))
        if range_val:
            cursor.execute("UPDATE services SET success_count = success_count + 1, updated_at = ? WHERE range_val = ?", 
                          (datetime.now().isoformat(), range_val))
        db.commit()
    except Exception as e:
        logging.error(f"DB Error inserting logs: {e}")
    
    country_code, flag_emoji = get_country_from_phone(phone)
    if not country_code:
        country_code = "GLOBAL"
        country_name = "Global"
        flag_emoji = "🌍"
    else:
        country_name = get_country_name(country_code)
    
    phone_side_id = "6204108584381322968" 
    otp_side_id = "5251203410396458957"
    globe_id = CUSTOM_EMOJIS.get("globe", "5447410659077661506")
    
    service_upper = service_name.upper()
    if service_upper == "NEW FB":
        display_svc, svc_emoji_id = "New FB", CUSTOM_EMOJIS.get("facebook", "5348125953090403204")
    elif service_upper == "WHATSAPP":
        display_svc, svc_emoji_id = "WhatsApp", CUSTOM_EMOJIS.get("whatsapp", "5416081784641168838")
    elif service_upper == "INSTAGRAM":
        display_svc, svc_emoji_id = "Instagram", CUSTOM_EMOJIS.get("instagram", "5332694612337244014")
    elif service_upper == "FACEBOOK":
        display_svc, svc_emoji_id = "Facebook", CUSTOM_EMOJIS.get("facebook", "5348125953090403204")
    else:
        display_svc, svc_emoji_id = service_name.title(), CUSTOM_EMOJIS.get("facebook", "5348125953090403204")
    
    text = (
        f"├── <tg-emoji emoji-id=\"{globe_id}\">🌐</tg-emoji> {flag_emoji} <b>{country_name}</b>\n"
        f"├── <tg-emoji emoji-id=\"{svc_emoji_id}\">📘</tg-emoji> <b>{display_svc}</b>\n"
        f"├── <tg-emoji emoji-id=\"{phone_side_id}\">📞</tg-emoji> <code>{phone}</code>\n"
        f"└── <tg-emoji emoji-id=\"{otp_side_id}\">🔑</tg-emoji> <code>{otp}</code>"
    )    
    try:
        await bot.send_message(user_id, text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Failed to send OTP to user {user_id}: {e}")
        fallback_text = (
            f"├── 🌐 {flag_emoji} <b>{country_name}</b>\n"
            f"├── 📘 <b>{display_svc}</b>\n"
            f"├── 📞 <code>{phone}</code>\n"
            f"└── 🔑 <code>{otp}</code>"
        )
        try:
            await bot.send_message(user_id, fallback_text, parse_mode="HTML")
        except:
            pass

    channel_id = cursor.execute("SELECT value FROM config WHERE key='otp_channel_id'").fetchone()
    if channel_id:
        try:
            await bot.send_message(int(channel_id[0]), text, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Failed to forward OTP to channel: {e}")

# ==================== ম্যানুয়াল OTP পোলিং ====================
async def poll_manual_otp(user_id: int, phone_number: str, service_name: str, start_time: float):
    end_time = start_time + 1200
    clean_phone = re.sub(r'\D', '', phone_number)
    while time.time() < end_time:
        row = cursor.execute("SELECT active_manual FROM users WHERE id=?", (user_id,)).fetchone()
        if not row or not row[0]:
            break
        cursor.execute(
            "SELECT otp_code FROM otp_success_logs WHERE user_id=? AND phone_number=? AND julianday(timestamp) >= julianday(?) ORDER BY timestamp DESC LIMIT 1",
            (user_id, clean_phone, datetime.fromtimestamp(start_time).isoformat())
        )
        result = cursor.fetchone()
        if result:
            await process_otp_reward(user_id, clean_phone, result[0], service_name=service_name)
            break
        await asyncio.sleep(2)
    if user_id in active_manual_pollers:
        active_manual_pollers[user_id] = [t for t in active_manual_pollers[user_id] if not t.done()]

async def process_manual_expiry():
    while True:
        try:
            now = time.time()
            rows = cursor.execute("SELECT id, active_manual FROM users WHERE active_manual IS NOT NULL").fetchall()
            for user_id, active_raw in rows:
                if not active_raw:
                    continue
                active = json.loads(active_raw)
                if now - active.get("buy_time", 0) > 1200:
                    nums = active.get("nums", [])
                    cursor.execute("UPDATE users SET active_manual=NULL WHERE id=?", (user_id,))
                    svc_id = active.get("svc_id")
                    if svc_id:
                        for num in nums:
                            cursor.execute("INSERT INTO manual_numbers (service_id, number) VALUES (?, ?)", (svc_id, num))
                        cursor.execute("UPDATE manual_services SET stock = stock + ? WHERE id=?", (len(nums), svc_id))
                    db.commit()
                    if user_id in active_manual_pollers:
                        for task in active_manual_pollers[user_id]:
                            task.cancel()
                        del active_manual_pollers[user_id]
                    try:
                        await bot.send_message(user_id, f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["warning"]}">⚠️</tg-emoji> আপনার ম্যানুয়াল নাম্বারের মেয়াদ শেষ হয়েছে।', parse_mode="HTML")
                    except:
                        pass
        except:
            pass
        await asyncio.sleep(60)

# ================= MENUS =================
def main_menu(user_id: int):
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text="GET NUMBER", icon_custom_emoji_id=CUSTOM_EMOJIS["phone"]),
        types.KeyboardButton(text="GET 2FA", icon_custom_emoji_id=CUSTOM_EMOJIS["lock"])
    )
    builder.row(
        types.KeyboardButton(text="EXTRACT OTP", icon_custom_emoji_id=CUSTOM_EMOJIS["folder"]),
        types.KeyboardButton(text="STATUS", icon_custom_emoji_id=CUSTOM_EMOJIS["chart"])
    )
    if is_admin(user_id):
        builder.row(types.KeyboardButton(text="ADMIN PANEL", icon_custom_emoji_id=CUSTOM_EMOJIS["gear"]))
    return builder.as_markup(resize_keyboard=True)

def get_number_main_menu():
    builder = InlineKeyboardBuilder()
    svc_config = {
        "FACEBOOK": CUSTOM_EMOJIS["facebook"],
        "WHATSAPP": CUSTOM_EMOJIS["whatsapp"],
        "INSTAGRAM": CUSTOM_EMOJIS["instagram"],
        "NEW FB": CUSTOM_EMOJIS["facebook"]
    }
    buttons = []
    for svc in ["FACEBOOK", "WHATSAPP", "INSTAGRAM", "NEW FB"]:
        display_name = "New FB" if svc == "NEW FB" else svc.title()
        buttons.append(types.InlineKeyboardButton(text=display_name, callback_data=f"view_svc_{svc}", icon_custom_emoji_id=svc_config[svc]))
    builder.row(buttons[0], buttons[1])
    builder.row(buttons[2], buttons[3])
    return builder.as_markup()

def admin_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="Add Service", callback_data="add_service", icon_custom_emoji_id=CUSTOM_EMOJIS["add"])
    builder.button(text="Add Manual Numbers", callback_data="add_manual_numbers", icon_custom_emoji_id=CUSTOM_EMOJIS["add"])
    builder.button(text="Manage Services", callback_data="manage_services", icon_custom_emoji_id=CUSTOM_EMOJIS["folder"])
    builder.button(text="Manage Admins", callback_data="manage_admins", icon_custom_emoji_id=CUSTOM_EMOJIS["users"])
    builder.button(text="Manage Manual Num.", callback_data="manage_manual_numbers", icon_custom_emoji_id=CUSTOM_EMOJIS["folder"])
    builder.button(text="Stats", callback_data="admin_stats", icon_custom_emoji_id=CUSTOM_EMOJIS["chart"])
    builder.button(text="Total Users", callback_data="total_users", icon_custom_emoji_id=CUSTOM_EMOJIS["users"])
    builder.button(text="Search User", callback_data="search_user", icon_custom_emoji_id=CUSTOM_EMOJIS["search"])
    builder.button(text="Set OTP Channel", callback_data="set_otp_channel", icon_custom_emoji_id=CUSTOM_EMOJIS["signal"])
    builder.button(text="Top 10 Users", callback_data="top_10_users", icon_custom_emoji_id=CUSTOM_EMOJIS["trophy"])
    builder.button(text="Broadcast", callback_data="admin_bc", icon_custom_emoji_id=CUSTOM_EMOJIS["broadcast"])
    builder.button(text="Ban User", callback_data="ban_user_btn", icon_custom_emoji_id=CUSTOM_EMOJIS["ban"])
    builder.button(text="Unban User", callback_data="unban_user_btn", icon_custom_emoji_id=CUSTOM_EMOJIS["success"])
    builder.button(text="Clear Auto Ranges", callback_data="clear_auto_services", icon_custom_emoji_id=CUSTOM_EMOJIS["delete"])
    current_m = "ON" if is_maintenance_mode() else "OFF"
    builder.button(text=f"Maintenance Mode [{current_m}]", callback_data="toggle_maintenance", icon_custom_emoji_id=CUSTOM_EMOJIS["maintenance"])
    builder.adjust(2)
    return builder.as_markup()

def admin_management_menu():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Add Admin", callback_data="add_admin_btn", icon_custom_emoji_id=CUSTOM_EMOJIS["add"]))
    builder.row(types.InlineKeyboardButton(text="Remove Admin", callback_data="remove_admin_btn", icon_custom_emoji_id=CUSTOM_EMOJIS["error"]))
    builder.row(types.InlineKeyboardButton(text="List Admins", callback_data="list_admins", icon_custom_emoji_id=CUSTOM_EMOJIS["folder"]))
    builder.row(types.InlineKeyboardButton(text="Back", callback_data="admin_back", icon_custom_emoji_id=CUSTOM_EMOJIS["back"]))
    return builder.as_markup()

# ================= HANDLERS =================
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    cursor.execute("INSERT OR IGNORE INTO users (id, username, fullname) VALUES (?, ?, ?)",
                   (message.from_user.id, message.from_user.username, message.from_user.full_name))
    db.commit()
    if await check_maintenance(message.from_user.id, message=message):
        return
    text = f"""
<tg-emoji emoji-id="{CUSTOM_EMOJIS['planet']}">🪐</tg-emoji>  <b><u>𝗙𝗔𝗦𝗧𝗫</u></b>
━━━━━━━━━━━━━━━━━━━━

👋 𝗛𝗘𝗟𝗟𝗢, <b>{message.from_user.first_name}</b>!

Get OTP codes instantly using virtual phone numbers — fast, reliable, global.

⚡ <b>Instant Delivery</b> · <tg-emoji emoji-id="{CUSTOM_EMOJIS['globe']}">🌐</tg-emoji> <b>Global Numbers</b>
🐱‍ <b>Auto OTP Detection</b>

━━━━━━━━━━━━━━━━━━━━
<tg-emoji emoji-id="{CUSTOM_EMOJIS['channel']}">📣</tg-emoji> <b>Channel:</b> @becup3290
<tg-emoji emoji-id="{CUSTOM_EMOJIS['chat']}">💬</tg-emoji> <b>Group:</b> @otpchannal1
━━━━━━━━━━━━━━━━━━━━
<tg-emoji emoji-id="{CUSTOM_EMOJIS['shopping']}">🛍️</tg-emoji> <b>Use the menu buttons below:</b>
"""
    await message.answer(text, reply_markup=main_menu(message.from_user.id), parse_mode="HTML")

@dp.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await send_home_view(callback)

@dp.callback_query(F.data == "back_to_get_number")
async def back_to_get_number(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await send_home_view(callback)

@dp.callback_query(F.data == "back_to_home")
async def back_to_home_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await send_home_view(callback)

@dp.callback_query(F.data == "back_to_services_menu")
async def back_to_services(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await send_home_view(callback)

async def send_home_view(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    text = f"""
<tg-emoji emoji-id="{CUSTOM_EMOJIS['planet']}">🪐</tg-emoji>  <b><u>𝗦𝗬 𝗦𝗦</u></b>
━━━━━━━━━━━━━━━━━━━━

👋 Hello, <b>{callback.from_user.first_name}</b>!

Get OTP codes instantly using virtual phone numbers — fast, reliable, global.

⚡ <b>Instant Delivery</b> · <tg-emoji emoji-id="{CUSTOM_EMOJIS['globe']}">🌐</tg-emoji> <b>Global Numbers</b>
🐱‍ <b>Auto OTP Detection</b>

━━━━━━━━━━━━━━━━━━━━
<tg-emoji emoji-id="{CUSTOM_EMOJIS['channel']}">📣</tg-emoji> <b>Channel:</b> @becup3290
<tg-emoji emoji-id="{CUSTOM_EMOJIS['chat']}">💬</tg-emoji> <b>Group:</b> @otpchannal1
━━━━━━━━━━━━━━━━━━━━
<tg-emoji emoji-id="{CUSTOM_EMOJIS['shopping']}">🛍️</tg-emoji> <b>Use the menu buttons below:</b>
"""
    await safe_edit_message(callback.message, text, reply_markup=main_menu(user_id), parse_mode="HTML")

@dp.message(F.text == "GET NUMBER")
async def get_number_selection(message: types.Message, state: FSMContext):
    await state.clear()
    if await check_maintenance(message.from_user.id, message=message):
        return
    success_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["success"]}">🟢</tg-emoji>'
    fb_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["facebook"]}">📘</tg-emoji>'
    wa_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["whatsapp"]}">🟢</tg-emoji>'
    ig_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["instagram"]}">🟣</tg-emoji>'
    skull_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["skull"]}">🧟</tg-emoji>'
    shop_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["shopping"]}">🛍️</tg-emoji>'
    text = (
        f"{success_tag} <b>Select a service</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"{fb_tag} Facebook  •  {wa_tag} WhatsApp\n"
        f"{ig_tag} Instagram •  {fb_tag} New FB\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"{skull_tag}{shop_tag} <i>Tap your desired service</i>"
    )
    await safe_send_message(message, text, reply_markup=get_number_main_menu(), parse_mode="HTML")

@dp.message(F.text == "GET 2FA")
async def get_2fa_prompt(message: types.Message, state: FSMContext):
    await state.clear()
    if await check_maintenance(message.from_user.id, message=message):
        return
    cat_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["cat"]}">🐱</tg-emoji>'
    phone_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["phone"]}">📱</tg-emoji>'
    wait_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["waiting"]}">⏳</tg-emoji>'
    shop_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["shopping"]}">🛍️</tg-emoji>'
    skull_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["skull"]}">💀</tg-emoji>'
    text = (
        f"{cat_tag}{phone_tag} <b>Get 2FA OTP</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"{cat_tag}{phone_tag} Paste your 2FA Secret Key below.\n\n"
        f"{wait_tag} <i>Example: JBSWY3DPEHPK3PXP</i>\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"{shop_tag}{skull_tag} <i>Paste the secret key to get your 6-digit OTP.</i>"
    )
    await safe_send_message(message, text, parse_mode="HTML")
    await state.set_state(UserStates.waiting_for_2fa)

@dp.message(UserStates.waiting_for_2fa)
async def process_2fa_live(message: types.Message, state: FSMContext):
    secret = message.text.strip().replace(" ", "").upper()
    try:
        totp = pyotp.TOTP(secret)
        current_otp = totp.now()
    except Exception:
        err_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["error"]}">❌</tg-emoji>'
        await safe_send_message(message, f"{err_tag} <b>ভুল Secret Key!</b> দয়া করে সঠিক 2FA Key দিন।", parse_mode="HTML")
        return
    await state.clear()
    suc_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["success"]}">✅</tg-emoji>'
    wait_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["waiting"]}">⏳</tg-emoji>'
    sent_msg = await safe_send_message(message,
        f"{suc_tag} <b>আপনার 2FA কোড:</b> <code>{current_otp}</code>\n\n"
        f"{wait_tag} <i>(কোডটি লাইভ আপডেট হচ্ছে...)</i>",
        parse_mode="HTML"
    )
    asyncio.create_task(update_2fa_message(sent_msg, secret))

async def update_2fa_message(message: types.Message, secret: str):
    totp = pyotp.TOTP(secret)
    suc_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["success"]}">✅</tg-emoji>'
    wait_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["waiting"]}">⏳</tg-emoji>'
    ban_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["ban"]}">🛑</tg-emoji>'
    for _ in range(10):
        try:
            time_remaining = 30 - (int(time.time()) % 30)
            await asyncio.sleep(time_remaining)
            new_otp = totp.now()
            await safe_edit_message(message,
                f"{suc_tag} <b>আপনার 2FA কোড:</b> <code>{new_otp}</code>\n\n"
                f"{wait_tag} <i>(কোডটি লাইভ আপডেট হচ্ছে...)</i>",
                parse_mode="HTML"
            )
        except Exception:
            break
    try:
        await safe_edit_message(message,
            f"{suc_tag} <b>আপনার শেষ 2FA কোড:</b> <code>{totp.now()}</code>\n\n"
            f"{ban_tag} <i>(৫ মিনিট হয়ে যাওয়ায় লাইভ আপডেট বন্ধ হয়েছে। আবার পেতে নতুন করে কি দিন।)</i>",
            parse_mode="HTML"
        )
    except:
        pass

@dp.message(F.text == "EXTRACT OTP")
async def extract_otp_handler(message: types.Message, state: FSMContext):
    await state.clear()
    if await check_maintenance(message.from_user.id, message=message):
        return
    uid = message.from_user.id
    rows = cursor.execute(
        "SELECT phone_number, otp_code, timestamp FROM otp_success_logs WHERE user_id=? AND timestamp >= datetime('now', '-1 day')",
        (uid,)
    ).fetchall()
    valid_rows = [(p, o, t) for p, o, t in rows if p and o]
    total_otp = len(valid_rows)
    if total_otp == 0:
        folder_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["folder"]}">📭</tg-emoji>'
        await safe_send_message(message, f"{folder_tag} গত ২৪ ঘণ্টায় আপনার কোনো সফল OTP হিস্ট্রি নেই বা ডেটা সেভ হয়নি।", parse_mode="HTML")
        return
    csv_buffer = StringIO()
    csv_writer = csv.writer(csv_buffer)
    csv_writer.writerow(['Phone Number', 'OTP', 'Time'])
    for phone, otp, time_stamp in valid_rows:
        csv_writer.writerow([phone, otp, time_stamp])
    csv_bytes = csv_buffer.getvalue().encode('utf-8')
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"otp_history_{timestamp_str}.csv"
    document = BufferedInputFile(csv_bytes, filename=file_name)
    cat_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["cat"]}">🐱</tg-emoji>'
    phone_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["phone"]}">📱</tg-emoji>'
    skull_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["skull"]}">😈</tg-emoji>'
    suc_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["success"]}">🌝</tg-emoji>'
    caption = (
        f"{cat_tag}{phone_tag} <b>OTP Export — Last 24 Hours</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"{cat_tag}{phone_tag} <b>Total OTP:</b> {total_otp}\n"
        f"{skull_tag} <b>Period:</b> Last 24 Hours\n\n"
        f"{suc_tag} <b>CSV file ready to download!</b>"
    )
    await message.answer_document(document=document, caption=caption, parse_mode="HTML")

@dp.message(F.text == "STATUS")
async def show_bot_stats(message: types.Message, state: FSMContext):
    await state.clear()
    if await check_maintenance(message.from_user.id, message=message):
        return
    top_countries = cursor.execute("""
        SELECT country_code, flag, COUNT(*) as cnt
        FROM services
        WHERE success_count > 0
        GROUP BY country_code
        ORDER BY cnt DESC LIMIT 5
    """).fetchall()
    country_text = ""
    if top_countries:
        for idx, (code, flag, cnt) in enumerate(top_countries, 1):
            custom_flag = get_custom_flag_emoji(code)
            country_text += f"{idx}. {custom_flag} {code} ➔ <code>+{code}</code> ({cnt} Hits)\n"
    else:
        country_text = "এখনো কোনো কান্ট্রির ডেটা নেই।\n"
    chart_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["chart"]}">📊</tg-emoji>'
    fire_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["fire"]}">🔥</tg-emoji>'
    trophy_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["trophy"]}">🏆</tg-emoji>'
    star_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["star"]}">🔹</tg-emoji>'
    info_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["info"]}">💡</tg-emoji>'
    text = (
        f"{chart_tag} <b>Network Statistics & Trends</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"{fire_tag} <b>Top Active Countries (Tap to Copy):</b>\n"
        f"{country_text}\n"
        f"{trophy_tag} <b>Most Active Services:</b>\n"
        f"{star_tag} Facebook ➔ <code>FACEBOOK</code>\n"
        f"{star_tag} Instagram ➔ <code>INSTAGRAM</code>\n"
        f"{star_tag} WhatsApp ➔ <code>WHATSAPP</code>\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"{info_tag} <i>Tip: Tap on any country code or service ID to copy it instantly!</i>"
    )
    await safe_send_message(message, text, parse_mode="HTML")

@dp.message(F.text == "ADMIN PANEL")
async def admin_panel_button(message: types.Message, state: FSMContext):
    await state.clear()
    if is_admin(message.from_user.id):
        gear_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["gear"]}">⚙️</tg-emoji>'
        await safe_send_message(message, f"{gear_tag} <b>ADMIN PANEL SYSTEM</b>", reply_markup=admin_menu(), parse_mode="HTML")

@dp.message(Command("admin"))
async def admin_main(message: types.Message, state: FSMContext):
    await state.clear()
    if is_admin(message.from_user.id):
        gear_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["gear"]}">⚙️</tg-emoji>'
        await safe_send_message(message, f"{gear_tag} <b>ADMIN PANEL SYSTEM</b>", reply_markup=admin_menu(), parse_mode="HTML")

# -------------------- Clear Auto Ranges --------------------
@dp.callback_query(F.data == "clear_auto_services")
async def clear_auto_services_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_admin(callback.from_user.id):
        await callback.answer("অননুমোদিত!", show_alert=True)
        return
    cursor.execute("DELETE FROM services")
    db.commit()
    suc_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["success"]}">✅</tg-emoji>'
    await callback.answer(f"{suc_tag} সমস্ত অটো রেঞ্জ সাফ করা হয়েছে!", show_alert=True)
    gear_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["gear"]}">⚙️</tg-emoji>'
    await safe_edit_message(callback.message, f"{gear_tag} <b>ADMIN PANEL SYSTEM</b>", reply_markup=admin_menu(), parse_mode="HTML")

# -------------------- Manage Services --------------------
@dp.callback_query(F.data == "manage_services")
async def manage_services(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_admin(callback.from_user.id):
        return
    rows = cursor.execute("SELECT id, name, flag, range_val, success_count FROM services ORDER BY name").fetchall()
    builder = InlineKeyboardBuilder()
    if rows:
        for sid, name, flag, rval, succ in rows:
            hot_mark = "🔥" if succ > 0 else ""
            builder.row(types.InlineKeyboardButton(text=f"🗑 {name} [{rval}] {hot_mark}", callback_data=f"del_srv_{sid}", icon_custom_emoji_id=CUSTOM_EMOJIS["delete"]))
    else:
        builder.row(types.InlineKeyboardButton(text="No services", callback_data="none", icon_custom_emoji_id=CUSTOM_EMOJIS["info"]))
    builder.row(types.InlineKeyboardButton(text="Clear All Ranges", callback_data="clear_all_ranges", icon_custom_emoji_id=CUSTOM_EMOJIS["delete"]))
    builder.row(types.InlineKeyboardButton(text="Add Service", callback_data="add_service", icon_custom_emoji_id=CUSTOM_EMOJIS["add"]))
    builder.row(types.InlineKeyboardButton(text="Back", callback_data="admin_back", icon_custom_emoji_id=CUSTOM_EMOJIS["back"]))
    folder_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["folder"]}">📂</tg-emoji>'
    await safe_edit_message(callback.message, f"{folder_tag} <b>Service List</b> (Click to delete):", reply_markup=builder.as_markup(), parse_mode="HTML")

# -------------------- Delete Service --------------------
@dp.callback_query(F.data.startswith("del_srv_"))
async def delete_service(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_admin(callback.from_user.id):
        return
    sid = int(callback.data.split("_")[-1])
    cursor.execute("DELETE FROM services WHERE id=?", (sid,))
    db.commit()
    suc_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["success"]}">✅</tg-emoji>'
    await callback.answer(f"{suc_tag} Service deleted successfully.", show_alert=True)
    await manage_services(callback, state)

# -------------------- Admin Handlers (Ban, Unban, Search, etc.) --------------------
@dp.callback_query(F.data == "ban_user_btn")
async def ban_user_start(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_admin(callback.from_user.id):
        return
    add_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["add"]}">✏️</tg-emoji>'
    await safe_edit_message(callback.message, f"{add_tag} Enter User ID to Ban:")
    await state.set_state(AdminStates.waiting_ban_user)
    await callback.answer()

@dp.message(AdminStates.waiting_ban_user)
async def process_ban_user(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    uid = message.text.strip()
    if not uid.isdigit():
        err_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["error"]}">❌</tg-emoji>'
        await safe_send_message(message, f"{err_tag} Invalid ID. Must be numeric.")
        return
    cursor.execute("UPDATE users SET is_banned=1 WHERE id=?", (uid,))
    db.commit()
    suc_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["success"]}">✅</tg-emoji>'
    await safe_send_message(message, f"{suc_tag} User <code>{uid}</code> has been banned.", parse_mode="HTML")
    await state.clear()

@dp.callback_query(F.data == "unban_user_btn")
async def unban_user_start(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_admin(callback.from_user.id):
        return
    add_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["add"]}">✏️</tg-emoji>'
    await safe_edit_message(callback.message, f"{add_tag} Enter User ID to Unban:")
    await state.set_state(AdminStates.waiting_unban_user)
    await callback.answer()

@dp.message(AdminStates.waiting_unban_user)
async def process_unban_user(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    uid = message.text.strip()
    if not uid.isdigit():
        err_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["error"]}">❌</tg-emoji>'
        await safe_send_message(message, f"{err_tag} Invalid ID. Must be numeric.")
        return
    cursor.execute("UPDATE users SET is_banned=0 WHERE id=?", (uid,))
    db.commit()
    suc_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["success"]}">✅</tg-emoji>'
    await safe_send_message(message, f"{suc_tag} User <code>{uid}</code> has been unbanned.", parse_mode="HTML")
    await state.clear()

@dp.callback_query(F.data == "search_user")
async def search_user_cb(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_admin(callback.from_user.id):
        return
    search_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["search"]}">🔍</tg-emoji>'
    await safe_edit_message(callback.message, f"{search_tag} অনুগ্রহ করে ইউজার আইডি বা ইউজারনেম লিখুন:")
    await state.set_state(AdminStates.waiting_search_user)
    await callback.answer()

@dp.message(AdminStates.waiting_search_user)
async def process_search_user(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    query = message.text.strip()
    err_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["error"]}">❌</tg-emoji>'
    search_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["search"]}">🔍</tg-emoji>'
    if query.isdigit():
        uid = int(query)
        row = cursor.execute("SELECT id, balance, username, fullname FROM users WHERE id=?", (uid,)).fetchone()
        if row:
            await show_userinfo_from_row(message, row)
        else:
            await safe_send_message(message, f"{err_tag} ইউজার পাওয়া যায়নি।")
    else:
        rows = cursor.execute("SELECT id, balance, username, fullname FROM users WHERE username LIKE ?", (f"%{query}%",)).fetchall()
        if rows:
            text = f"{search_tag} <b>Search Results:</b>\n\n"
            for r in rows:
                text += f"• <code>{r[0]}</code> @{r[2]}\n"
            await safe_send_message(message, text, parse_mode="HTML")
        else:
            await safe_send_message(message, f"{err_tag} কোনো ইউজার পাওয়া যায়নি।")
    await state.clear()

@dp.message(Command("userinfo"))
async def userinfo_command(message: types.Message, state: FSMContext):
    await state.clear()
    if not is_admin(message.from_user.id):
        return
    args = message.text.split()
    if len(args) < 2:
        await safe_send_message(message, "Usage: /userinfo <user_id>")
        return
    uid = args[1]
    if not uid.isdigit():
        await safe_send_message(message, "Invalid user ID.")
        return
    row = cursor.execute("SELECT id, balance, username, fullname FROM users WHERE id=?", (int(uid),)).fetchone()
    if row:
        await show_userinfo_from_row(message, row)
    else:
        await safe_send_message(message, "User not found.")

async def show_userinfo_from_row(message: types.Message, row):
    uid, _, uname, fullname = row
    total_otp = cursor.execute("SELECT COUNT(*) FROM otp_success_logs WHERE user_id=?", (uid,)).fetchone()[0]
    banned_status = "Yes" if is_banned(uid) else "No"
    user_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["users"]}">👤</tg-emoji>'
    text = (
        f"{user_tag} <b>User Dashboard Info</b>\n\n"
        f"<b>ID:</b> <code>{uid}</code>\n"
        f"<b>Name:</b> {fullname}\n"
        f"<b>Username:</b> @{uname}\n"
        f"<b>Total OTPs:</b> {total_otp}\n"
        f"<b>Banned:</b> {banned_status}\n"
    )
    await safe_send_message(message, text, parse_mode="HTML")

@dp.callback_query(F.data == "admin_stats")
async def admin_stats_cb(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_admin(callback.from_user.id):
        return
    total_users = cursor.execute("SELECT COUNT(id) FROM users").fetchone()[0]
    today = datetime.now().strftime("%Y-%m-%d")
    today_otp = cursor.execute("SELECT COUNT(*) FROM otp_success_logs WHERE timestamp LIKE ?", (f"{today}%",)).fetchone()[0]
    chart_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["chart"]}">📊</tg-emoji>'
    user_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["users"]}">👥</tg-emoji>'
    email_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["email"]}">📨</tg-emoji>'
    text = (
        f"{chart_tag} <b>System Live Stats</b>\n\n"
        f"{user_tag} <b>Total Users:</b> {total_users}\n"
        f"{email_tag} <b>Today's Success OTP:</b> {today_otp}\n"
    )
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Back", callback_data="admin_back", icon_custom_emoji_id=CUSTOM_EMOJIS["back"]))
    await safe_edit_message(callback.message, text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "set_otp_channel")
async def set_otp_channel_cb(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_admin(callback.from_user.id):
        return
    signal_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["signal"]}">📡</tg-emoji>'
    await safe_edit_message(callback.message, f"{signal_tag} লাইভ ওটিপি ফিড যেই চ্যানেলে পাঠাতে চান, তার চ্যানেল আইডি দিন:")
    await state.set_state(AdminStates.waiting_otp_channel)
    await callback.answer()

@dp.message(AdminStates.waiting_otp_channel)
async def save_otp_channel(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    channel_id = message.text.strip()
    if channel_id.startswith("-100") and channel_id[1:].isdigit():
        cursor.execute("INSERT OR REPLACE INTO config (key, value) VALUES ('otp_channel_id', ?)", (channel_id,))
        db.commit()
        suc_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["success"]}">✅</tg-emoji>'
        await safe_send_message(message, f"{suc_tag} লাইভ ওটিপি ফিড চ্যানেল সেট করা হয়েছে: <code>{channel_id}</code>", parse_mode="HTML")
        await state.clear()
    else:
        err_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["error"]}">❌</tg-emoji>'
        await safe_send_message(message, f"{err_tag} বৈধ চ্যানেল আইডি দিন (-100... ফরম্যাটে)।")

@dp.callback_query(F.data.startswith("view_svc_"))
async def view_service_countries(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    svc_name = callback.data.replace("view_svc_", "")
    manuals = cursor.execute("SELECT id, country_name, flag, stock FROM manual_services WHERE service_name=? AND stock > 0", (svc_name.upper(),)).fetchall()
    ranges = cursor.execute("SELECT DISTINCT country_code, flag, COUNT(*) as cnt FROM services WHERE name=? GROUP BY country_code ORDER BY cnt DESC", (svc_name.upper(),)).fetchall()
    count_live = len(manuals) + len(ranges)
    now_str = datetime.now().strftime("%I:%M:%S %p")
    globe_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["globe"]}">🌐</tg-emoji>'
    red_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["red_circle"]}">🔴</tg-emoji>'
    shop_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["shopping"]}">🛍️</tg-emoji>'
    refresh_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["refresh"]}">🔄</tg-emoji>'
    text = (
        f"{globe_tag} <b>{svc_name.upper()}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{red_tag} 𝗟𝗜𝗩𝗘: <b>Countries available</b>\n\n"
        f"{shop_tag} <i>Select a country to get number</i>\n"
        f"{refresh_tag} <i>Updated: {now_str}</i>"
    )
    builder = InlineKeyboardBuilder()
    for svc_id, c_name, flag, stock in manuals:
        builder.row(types.InlineKeyboardButton(
            text=f"{c_name} (Premium: {stock})",
            callback_data=f"man_cntry_{svc_id}",
            icon_custom_emoji_id=CUSTOM_EMOJIS["package"]
        ))
    for ccode, flag, cnt in ranges:
        button_icon_id = get_custom_flag_icon_id(ccode)
        country_full = get_country_name(ccode)
        builder.row(types.InlineKeyboardButton(
            text=f"{country_full}",
            callback_data=f"cntry_{svc_name}_{ccode}",
            icon_custom_emoji_id=button_icon_id
        ))
    if count_live == 0:
        builder.row(types.InlineKeyboardButton(text="No Countries Available", callback_data="none", icon_custom_emoji_id=CUSTOM_EMOJIS["ban"]))
    builder.row(
        types.InlineKeyboardButton(text="Refresh", callback_data=f"view_svc_{svc_name}", icon_custom_emoji_id=CUSTOM_EMOJIS["refresh"]),
        types.InlineKeyboardButton(text="Back", callback_data="back_to_services_menu", icon_custom_emoji_id=CUSTOM_EMOJIS["back"])
    )
    try:
        await safe_edit_message(callback.message, text, reply_markup=builder.as_markup(), parse_mode="HTML")
    except:
        try:
            await safe_send_message(callback.message, text, reply_markup=builder.as_markup(), parse_mode="HTML")
        except:
            pass
    await callback.answer("Refreshed!")

@dp.callback_query(F.data.startswith("cntry_"))
async def auto_fetch_country_range(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if await check_maintenance(callback.from_user.id, callback=callback):
        return
    parts = callback.data.split("_")
    service_name = parts[1]
    country_code = parts[2]
    best_range_row = cursor.execute(
        "SELECT range_val FROM services WHERE name=? AND country_code=? ORDER BY updated_at DESC, success_count DESC, is_hot DESC LIMIT 1",
        (service_name, country_code)
    ).fetchone()
    if not best_range_row:
        err_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["error"]}">❌</tg-emoji>'
        await callback.answer(f"{err_tag} এই কান্ট্রির কোনো একটিভ রেঞ্জ পাওয়া যায়নি!", show_alert=True)
        return
    range_val = best_range_row[0]
    await send_range_numbers_message(callback, range_val, limit=3)

@dp.callback_query(F.data.startswith("use_range_"))
async def fetch_number_by_range(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    range_val = callback.data[10:]
    if await check_maintenance(callback.from_user.id, callback=callback):
        return
    await send_range_numbers_message(callback, range_val, limit=3)

@dp.callback_query(F.data == "top_10_users")
async def show_top_10_users(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_admin(callback.from_user.id):
        return
    thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
    try:
        cursor.execute("DELETE FROM otp_success_logs WHERE timestamp < ?", (thirty_days_ago,))
        db.commit()
    except:
        pass
    cursor.execute("""
        SELECT u.fullname, u.username, COUNT(o.id) as otp_count
        FROM otp_success_logs o
        JOIN users u ON o.user_id = u.id
        WHERE o.timestamp >= ?
        GROUP BY o.user_id
        ORDER BY otp_count DESC
        LIMIT 10
    """, (thirty_days_ago,))
    rows = cursor.fetchall()
    trophy_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["trophy"]}">🏆</tg-emoji>'
    if not rows:
        text = f"{trophy_tag} <b>Top 10 Users (Last 30 Days)</b>\n\nকোনো ইউজারের সফল OTP হিস্ট্রি পাওয়া যায়নি।"
    else:
        text = f"{trophy_tag} <b>Top 10 Users (Last 30 Days)</b>\n\n"
        medals = [CUSTOM_EMOJIS["trophy"], "5447203607294265305", "5453902265922376865"]
        for idx, row in enumerate(rows):
            fullname = row[0] or "Unknown"
            username = f"(@{row[1]})" if row[1] else ""
            if idx < 3:
                rank = f'<tg-emoji emoji-id="{medals[idx]}">🏅</tg-emoji>'
            else:
                rank = f"<code>{idx+1}.</code>"
            text += f"{rank} {fullname} {username} - <code>{row[2]} OTP</code>\n"
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Back", callback_data="admin_back", icon_custom_emoji_id=CUSTOM_EMOJIS["back"]))
    await safe_edit_message(callback.message, text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "total_users")
async def show_total_users(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_admin(callback.from_user.id):
        return
    count = cursor.execute("SELECT COUNT(id) FROM users").fetchone()[0]
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Back", callback_data="admin_back", icon_custom_emoji_id=CUSTOM_EMOJIS["back"]))
    user_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["users"]}">👥</tg-emoji>'
    await safe_edit_message(callback.message, f"{user_tag} <b>Total Registered Users:</b> <code>{count}</code>", reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "clear_all_ranges")
async def clear_all_ranges(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_admin(callback.from_user.id):
        return
    cursor.execute("DELETE FROM services")
    db.commit()
    suc_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["success"]}">✅</tg-emoji>'
    await callback.answer(f"{suc_tag} All ranges have been cleared successfully!", show_alert=True)
    await manage_services(callback, state)

@dp.callback_query(F.data == "manage_admins")
async def manage_admins_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_admin(callback.from_user.id):
        return
    user_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["users"]}">👥</tg-emoji>'
    await safe_edit_message(callback.message, f"{user_tag} <b>Admin Management Systems</b>:", reply_markup=admin_management_menu(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "add_admin_btn")
async def add_admin_prompt(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_admin(callback.from_user.id):
        return
    add_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["add"]}">✏️</tg-emoji>'
    await safe_edit_message(callback.message, f"{add_tag} Enter the User ID to add as Admin:")
    await state.set_state(AdminStates.waiting_add_admin)
    await callback.answer()

@dp.message(AdminStates.waiting_add_admin)
async def add_admin(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    uid = message.text.strip()
    if not uid.isdigit():
        err_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["error"]}">❌</tg-emoji>'
        await safe_send_message(message, f"{err_tag} Invalid ID.")
        return
    cursor.execute("INSERT OR IGNORE INTO admins VALUES (?)", (uid,))
    db.commit()
    suc_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["success"]}">✅</tg-emoji>'
    await safe_send_message(message, f"{suc_tag} User <code>{uid}</code> is now an admin.", parse_mode="HTML")
    await state.clear()

@dp.callback_query(F.data == "remove_admin_btn")
async def remove_admin_prompt(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_admin(callback.from_user.id):
        return
    add_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["add"]}">✏️</tg-emoji>'
    await safe_edit_message(callback.message, f"{add_tag} Enter the User ID to remove from Admins:")
    await state.set_state(AdminStates.waiting_remove_admin)
    await callback.answer()

@dp.message(AdminStates.waiting_remove_admin)
async def remove_admin(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    uid = message.text.strip()
    if uid == str(message.from_user.id):
        err_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["error"]}">❌</tg-emoji>'
        await safe_send_message(message, f"{err_tag} You cannot remove yourself.")
        return
    cursor.execute("DELETE FROM admins WHERE user_id=?", (uid,))
    db.commit()
    suc_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["success"]}">✅</tg-emoji>'
    await safe_send_message(message, f"{suc_tag} User <code>{uid}</code> is no longer an admin.", parse_mode="HTML")
    await state.clear()

@dp.callback_query(F.data == "list_admins")
async def list_admins(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_admin(callback.from_user.id):
        return
    rows = cursor.execute("SELECT user_id FROM admins").fetchall()
    user_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["users"]}">👥</tg-emoji>'
    if rows:
        items = "".join([f"• <code>{uid}</code>\n" for (uid,) in rows])
        text = f"{user_tag} <b>Current Active Admins:</b>\n\n{items}"
    else:
        text = f"{user_tag} <b>Current Active Admins:</b>\n\nNo admins found."
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Back", callback_data="manage_admins", icon_custom_emoji_id=CUSTOM_EMOJIS["back"]))
    await safe_edit_message(callback.message, text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "admin_bc")
async def bc_start(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_admin(callback.from_user.id):
        return
    add_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["add"]}">✏️</tg-emoji>'
    await safe_edit_message(callback.message, f"{add_tag} Send the broadcast message (text, photo, video, etc.):")
    await state.set_state(AdminStates.waiting_broadcast)
    await callback.answer()

@dp.message(AdminStates.waiting_broadcast)
async def bc_send(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    users = cursor.execute("SELECT id FROM users").fetchall()
    success = 0
    wait_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["waiting"]}">⏳</tg-emoji>'
    await safe_send_message(message, f"{wait_tag} Sending broadcast...")
    for (uid,) in users:
        try:
            await bot.copy_message(chat_id=int(uid), from_chat_id=message.chat.id, message_id=message.message_id)
            success += 1
            await asyncio.sleep(0.1)
        except:
            pass
    suc_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["success"]}">✅</tg-emoji>'
    await safe_send_message(message, f"{suc_tag} Broadcast sent successfully to {success} users.")
    await state.clear()

@dp.callback_query(F.data == "admin_back")
async def admin_back(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if is_admin(callback.from_user.id):
        await callback.answer()
        gear_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["gear"]}">⚙️</tg-emoji>'
        await safe_edit_message(callback.message, f"{gear_tag} <b>ADMIN PANEL SYSTEM</b>", reply_markup=admin_menu(), parse_mode="HTML")

@dp.callback_query(F.data == "close_admin_panel")
async def close_admin_panel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if is_admin(callback.from_user.id):
        await callback.answer()
        await callback.message.delete()

@dp.callback_query(F.data == "toggle_maintenance")
async def toggle_maintenance(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized!", show_alert=True)
        return
    current = is_maintenance_mode()
    new_value = "off" if current else "on"
    cursor.execute("UPDATE config SET value=? WHERE key='maintenance_mode'", (new_value,))
    db.commit()
    status_text = "ON" if new_value == "on" else "OFF"
    await callback.answer(f"Maintenance mode turned {status_text}", show_alert=True)
    gear_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["gear"]}">⚙️</tg-emoji>'
    await safe_edit_message(callback.message, f"{gear_tag} <b>ADMIN PANEL SYSTEM</b>", reply_markup=admin_menu(), parse_mode="HTML")

@dp.callback_query(F.data == "add_service")
async def add_service_start(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_admin(callback.from_user.id):
        return
    add_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["add"]}">✏️</tg-emoji>'
    await safe_edit_message(callback.message, f"{add_tag} Enter service name (e.g. WHATSAPP):")
    await state.set_state(AdminStates.waiting_service_name)
    await callback.answer()

@dp.message(AdminStates.waiting_service_name)
async def service_name(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(svc_name=message.text.strip().upper())
    add_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["add"]}">✏️</tg-emoji>'
    await safe_send_message(message, f"{add_tag} Enter range value (e.g. 99298XXX):")
    await state.set_state(AdminStates.waiting_range_val)

@dp.message(AdminStates.waiting_range_val)
async def service_range(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(svc_range=message.text.strip())
    add_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["add"]}">✏️</tg-emoji>'
    await safe_send_message(message, f"{add_tag} Enter country code (e.g. TJ):")
    await state.set_state(AdminStates.waiting_country_code)

@dp.message(AdminStates.waiting_country_code)
async def service_country(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    country_code = message.text.strip().upper()
    flag = get_custom_flag_emoji(country_code)
    exist = cursor.execute("SELECT id FROM services WHERE range_val=?", (data['svc_range'],)).fetchone()
    if exist:
        err_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["error"]}">❌</tg-emoji>'
        await safe_send_message(message, f"{err_tag} Range already exists.")
        await state.clear()
        return
    now_time = datetime.now().isoformat()
    cursor.execute("INSERT INTO services (name, range_val, country_code, flag, is_hot, updated_at) VALUES (?,?,?,?,0,?)",
                   (data['svc_name'], data['svc_range'], country_code, flag, now_time))
    db.commit()
    suc_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["success"]}">✅</tg-emoji>'
    await safe_send_message(message, f"{suc_tag} Service {data['svc_name']} added successfully.")
    await state.clear()

@dp.callback_query(F.data == "add_manual_numbers")
async def add_manual_start(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_admin(callback.from_user.id):
        return
    folder_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["folder"]}">📂</tg-emoji>'
    await safe_edit_message(callback.message, f"{folder_tag} Send a .txt file with one phone number per line:")
    await state.set_state(AdminStates.waiting_manual_file)
    await callback.answer()

@dp.message(AdminStates.waiting_manual_file, F.document)
async def manual_file_received(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    doc = message.document
    if not doc.file_name.endswith('.txt'):
        err_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["error"]}">❌</tg-emoji>'
        await safe_send_message(message, f"{err_tag} Only .txt files accepted.")
        return
    try:
        file = await bot.get_file(doc.file_id)
        downloaded = await bot.download_file(file.file_path)
        content = downloaded.read().decode('utf-8', errors='ignore')
    except Exception as e:
        err_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["error"]}">❌</tg-emoji>'
        await safe_send_message(message, f"{err_tag} File read error: {e}")
        await state.clear()
        return
    numbers = [line.strip() for line in content.strip().split('\n') if line.strip()]
    if not numbers:
        await safe_send_message(message, "No valid numbers found.")
        await state.clear()
        return
    await state.update_data(manual_numbers=numbers)
    add_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["add"]}">✏️</tg-emoji>'
    await safe_send_message(message, f"{add_tag} Enter service name (e.g., WHATSAPP, FACEBOOK, INSTAGRAM, NEW FB):")
    await state.set_state(AdminStates.waiting_manual_svc_name)

@dp.message(AdminStates.waiting_manual_svc_name)
async def manual_svc_name(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(manual_svc=message.text.strip().upper())
    globe_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["globe"]}">🌍</tg-emoji>'
    await safe_send_message(message, f"{globe_tag} Enter country name (e.g., Bangladesh):")
    await state.set_state(AdminStates.waiting_manual_country)

@dp.message(AdminStates.waiting_manual_country)
async def manual_country(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(manual_country=message.text.strip())
    add_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["add"]}">✏️</tg-emoji>'
    await safe_send_message(message, f"{add_tag} How many numbers to give per click? (e.g. 3):")
    await state.set_state(AdminStates.waiting_manual_give_amount)

@dp.message(AdminStates.waiting_manual_give_amount)
async def manual_give_amount(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        give = int(message.text)
        if give < 1:
            raise ValueError
    except ValueError:
        err_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["error"]}">❌</tg-emoji>'
        await safe_send_message(message, f"{err_tag} Enter a positive number.")
        return
    await state.update_data(manual_give=give)
    wait_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["waiting"]}">⏱</tg-emoji>'
    await safe_send_message(message, f"{wait_tag} Enter Cooldown Time for users (in seconds, e.g. 60):")
    await state.set_state(AdminStates.waiting_manual_cooldown)

@dp.message(AdminStates.waiting_manual_cooldown)
async def manual_cooldown_save(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        cooldown = int(message.text)
        if cooldown < 0:
            raise ValueError
    except ValueError:
        err_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["error"]}">❌</tg-emoji>'
        await safe_send_message(message, f"{err_tag} Enter a valid number for seconds.")
        return
    data = await state.get_data()
    svc = data['manual_svc']
    country = data['manual_country']
    give = data['manual_give']
    numbers = data['manual_numbers']
    flag = get_custom_flag_emoji(country) if country else ""
    cursor.execute("INSERT INTO manual_services (service_name, country_name, flag, give_amount, otp_rate, stock, cooldown) VALUES (?,?,?,?,?,?,?)",
                   (svc, country, flag, give, 0.0, len(numbers), cooldown))
    svc_id = cursor.lastrowid
    for num in numbers:
        cursor.execute("INSERT INTO manual_numbers (service_id, number) VALUES (?,?)", (svc_id, num))
    db.commit()
    suc_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["success"]}">✅</tg-emoji>'
    text = f"{suc_tag} Added {len(numbers)} numbers to {svc} - {country} with {cooldown}s cooldown.\n\nDo you want to broadcast this to users?"
    builder = InlineKeyboardBuilder()
    builder.button(text="Broadcast", callback_data=f"m_bc_{svc_id}", icon_custom_emoji_id=CUSTOM_EMOJIS["broadcast"])
    builder.button(text="Close", callback_data="close_admin_panel", icon_custom_emoji_id=CUSTOM_EMOJIS["error"])
    await safe_send_message(message, text, reply_markup=builder.as_markup())
    await state.clear()

@dp.callback_query(F.data.startswith("m_bc_"))
async def broadcast_manual_addition(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_admin(callback.from_user.id):
        return
    svc_id = int(callback.data.split("_")[2])
    svc_row = cursor.execute("SELECT service_name, country_name, flag, stock FROM manual_services WHERE id=?", (svc_id,)).fetchone()
    if not svc_row:
        await callback.answer("Service not found.", show_alert=True)
        return
    svc, country, flag, stock = svc_row
    fire_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["fire"]}">🔥</tg-emoji>'
    folder_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["folder"]}">📂</tg-emoji>'
    globe_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["globe"]}">🌍</tg-emoji>'
    chart_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["chart"]}">📊</tg-emoji>'
    next_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["next"]}">🚀</tg-emoji>'
    bc_text = (
        f"{fire_tag} <b>নিউ নাম্বার এড করা হয়েছে</b> {fire_tag}\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"{folder_tag} <b>Service:</b> {svc}\n"
        f"{globe_tag} <b>Country:</b> {flag} {country}\n"
        f"{chart_tag} <b>Stock Added:</b> {stock} numbers\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"{next_tag} Go to <b>GET NUMBER</b> and grab yours now!"
    )
    wait_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["waiting"]}">⏳</tg-emoji>'
    await safe_edit_message(callback.message, f"{wait_tag} Sending broadcast...")
    users = cursor.execute("SELECT id FROM users").fetchall()
    success = 0
    for (uid,) in users:
        try:
            await bot.send_message(int(uid), bc_text, parse_mode="HTML")
            success += 1
            await asyncio.sleep(0.1)
        except:
            pass
    suc_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["success"]}">✅</tg-emoji>'
    await safe_edit_message(callback.message, f"{suc_tag} Broadcast sent successfully to {success} users.")

@dp.callback_query(F.data == "manage_manual_numbers")
async def manage_manual_numbers(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_admin(callback.from_user.id):
        return
    services = cursor.execute("SELECT id, service_name, country_name, stock FROM manual_services").fetchall()
    if not services:
        await callback.answer("No manual services.", show_alert=True)
        return
    builder = InlineKeyboardBuilder()
    for svc_id, svc, country, stock in services:
        builder.row(types.InlineKeyboardButton(text=f"{svc} - {country} ({stock} left)", callback_data=f"del_manual_{svc_id}", icon_custom_emoji_id=CUSTOM_EMOJIS["delete"]))
    builder.row(types.InlineKeyboardButton(text="Back", callback_data="admin_back", icon_custom_emoji_id=CUSTOM_EMOJIS["back"]))
    folder_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["folder"]}">📋</tg-emoji>'
    await safe_edit_message(callback.message, f"{folder_tag} Manual services - click to delete:", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("del_manual_"))
async def delete_manual_service(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_admin(callback.from_user.id):
        return
    svc_id = int(callback.data[11:])
    cursor.execute("DELETE FROM manual_numbers WHERE service_id=?", (svc_id,))
    cursor.execute("DELETE FROM manual_services WHERE id=?", (svc_id,))
    db.commit()
    await callback.answer("Deleted.", show_alert=True)
    await manage_manual_numbers(callback, state)

@dp.callback_query(F.data.startswith("man_cntry_"))
async def manual_country_selected(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if await check_maintenance(callback.from_user.id, callback=callback):
        return
    svc_id = int(callback.data[10:])
    uid = callback.from_user.id
    wait_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["waiting"]}">⏳</tg-emoji>'
    fetching_msg = await safe_edit_message(callback.message, f"{wait_tag} <b>Fetching numbers, please wait...</b>", parse_mode="HTML")
    svc_row = cursor.execute("SELECT service_name, country_name, give_amount, stock, flag, cooldown FROM manual_services WHERE id=? AND stock > 0", (svc_id,)).fetchone()
    if not svc_row:
        await safe_edit_message(fetching_msg, f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["error"]}">❌</tg-emoji> Service not available.')
        return
    svc_name, c_name, give_amount, stock, flag, cooldown = svc_row
    user_cd_raw = cursor.execute("SELECT manual_cooldowns FROM users WHERE id=?", (uid,)).fetchone()
    user_cds = json.loads(user_cd_raw[0]) if user_cd_raw and user_cd_raw[0] else {}
    last_time = user_cds.get(str(svc_id), 0)
    if time.time() - last_time < cooldown:
        wait_sec = int(cooldown - (time.time() - last_time))
        await safe_edit_message(fetching_msg, f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["waiting"]}">⏳</tg-emoji> আপনি {wait_sec} সেকেন্ড পর নাম্বার নিতে পারবেন।')
        return
    nums_rows = cursor.execute("SELECT number FROM manual_numbers WHERE service_id=? ORDER BY RANDOM() LIMIT ?", (svc_id, give_amount)).fetchall()
    nums = [r[0] for r in nums_rows]
    if len(nums) < give_amount:
        await safe_edit_message(fetching_msg, f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["error"]}">❌</tg-emoji> Not enough numbers in stock.')
        return
    cursor.execute("DELETE FROM manual_numbers WHERE service_id=? AND number IN ({})".format(','.join('?'*len(nums))), (svc_id, *nums))
    cursor.execute("UPDATE manual_services SET stock = stock - ? WHERE id=?", (give_amount, svc_id))
    active_data = json.dumps({"svc_id": svc_id, "svc": svc_name, "c": c_name, "nums": nums, "buy_time": time.time()})
    user_cds[str(svc_id)] = time.time()
    cursor.execute("UPDATE users SET active_manual=?, manual_cooldowns=? WHERE id=?", (active_data, json.dumps(user_cds), uid))
    db.commit()
    if uid in active_manual_pollers:
        for t in active_manual_pollers[uid]:
            t.cancel()
        active_manual_pollers[uid] = []
    start_time = time.time()
    poll_tasks = []
    for num in nums:
        task = asyncio.create_task(poll_manual_otp(uid, num, svc_name, start_time))
        poll_tasks.append(task)
    active_manual_pollers[uid] = poll_tasks
    svc_emojis = {"FACEBOOK": CUSTOM_EMOJIS['facebook'], "WHATSAPP": CUSTOM_EMOJIS['whatsapp'],
                  "INSTAGRAM": CUSTOM_EMOJIS['instagram'], "NEW FB": CUSTOM_EMOJIS['facebook']}
    service_icon_id = svc_emojis.get(svc_name.upper(), CUSTOM_EMOJIS['phone'])
    globe_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["globe"]}">🌐</tg-emoji>'
    text = (
        f"{globe_tag} <b>Country :</b> {flag} {c_name}\n"
        f"{wait_tag} <i>Waiting for OTP</i>"
    )
    builder = InlineKeyboardBuilder()
    for num in nums:
        builder.row(InlineKeyboardButton(text=f"⎘ {num}", copy_text=CopyTextButton(text=str(num)), icon_custom_emoji_id=service_icon_id))
    builder.row(InlineKeyboardButton(text="Change Number", callback_data=f"man_change_{svc_id}", icon_custom_emoji_id=CUSTOM_EMOJIS['next']))
    builder.row(InlineKeyboardButton(text="Change Country", callback_data=f"view_svc_{svc_name}", icon_custom_emoji_id=CUSTOM_EMOJIS['globe']))
    builder.row(InlineKeyboardButton(text="Home", callback_data="back_to_home", icon_custom_emoji_id=CUSTOM_EMOJIS['store']),
                InlineKeyboardButton(text="OTP Group ", url=OTP_GROUP_LINK, icon_custom_emoji_id=CUSTOM_EMOJIS['chat']))
    await safe_edit_message(fetching_msg, text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data.startswith("man_change_"))
async def man_change_numbers(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if await check_maintenance(callback.from_user.id, callback=callback):
        return
    svc_id = int(callback.data.split("_")[-1])
    uid = callback.from_user.id
    active_row = cursor.execute("SELECT active_manual FROM users WHERE id=?", (uid,)).fetchone()
    if not active_row or not active_row[0]:
        await callback.answer("No active manual numbers to change.", show_alert=True)
        return
    active = json.loads(active_row[0])
    if active.get("svc_id") != svc_id:
        await callback.answer("Cannot change different service.", show_alert=True)
        return
    svc_row = cursor.execute("SELECT service_name, country_name, give_amount, flag, cooldown FROM manual_services WHERE id=?", (svc_id,)).fetchone()
    if not svc_row:
        return
    svc_name, c_name, give_amount, flag, cooldown = svc_row
    user_cd_raw = cursor.execute("SELECT manual_cooldowns FROM users WHERE id=?", (uid,)).fetchone()
    user_cds = json.loads(user_cd_raw[0]) if user_cd_raw and user_cd_raw[0] else {}
    last_time = user_cds.get(str(svc_id), 0)
    elapsed = time.time() - last_time
    if elapsed < cooldown:
        wait_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["waiting"]}">⏳</tg-emoji>'
        await callback.answer(f"{wait_tag} আপনি {int(cooldown - elapsed)}s পর চেঞ্জ করতে পারবেন।", show_alert=True)
        return
    wait_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["waiting"]}">⏳</tg-emoji>'
    fetching_msg = await safe_edit_message(callback.message, f"{wait_tag} <b>Fetching new numbers, please wait...</b>", parse_mode="HTML")
    old_nums = active.get("nums", [])
    for num in old_nums:
        cursor.execute("INSERT INTO manual_numbers (service_id, number) VALUES (?, ?)", (svc_id, num))
    if old_nums:
        placeholders = ','.join(['?'] * len(old_nums))
        query = f"SELECT number FROM manual_numbers WHERE service_id=? AND number NOT IN ({placeholders}) ORDER BY RANDOM() LIMIT ?"
        params = [svc_id] + old_nums + [give_amount]
    else:
        query = "SELECT number FROM manual_numbers WHERE service_id=? ORDER BY RANDOM() LIMIT ?"
        params = [svc_id, give_amount]
    new_nums = cursor.execute(query, params).fetchall()
    new_nums = [r[0] for r in new_nums]
    if len(new_nums) < give_amount:
        new_nums = cursor.execute("SELECT number FROM manual_numbers WHERE service_id=? ORDER BY RANDOM() LIMIT ?", (svc_id, give_amount)).fetchall()
        new_nums = [r[0] for r in new_nums]
    if len(new_nums) < give_amount:
        err_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["error"]}">❌</tg-emoji>'
        await safe_edit_message(fetching_msg, f"{err_tag} স্টকে আর কোনো নাম্বার নেই!")
        cursor.execute("UPDATE users SET active_manual=NULL WHERE id=?", (uid,))
        db.commit()
        return
    placeholders = ','.join(['?'] * len(new_nums))
    cursor.execute(f"DELETE FROM manual_numbers WHERE service_id=? AND number IN ({placeholders})", (svc_id, *new_nums))
    active["nums"] = new_nums
    active["buy_time"] = time.time()
    user_cds[str(svc_id)] = time.time()
    cursor.execute("UPDATE users SET active_manual=?, manual_cooldowns=? WHERE id=?", (json.dumps(active), json.dumps(user_cds), uid))
    db.commit()
    if uid in active_manual_pollers:
        for t in active_manual_pollers[uid]:
            t.cancel()
        active_manual_pollers[uid] = []
    start_time = time.time()
    poll_tasks = []
    for num in new_nums:
        task = asyncio.create_task(poll_manual_otp(uid, num, svc_name, start_time))
        poll_tasks.append(task)
    active_manual_pollers[uid] = poll_tasks
    svc_emojis = {"FACEBOOK": CUSTOM_EMOJIS["facebook"], "WHATSAPP": CUSTOM_EMOJIS["whatsapp"],
                  "INSTAGRAM": CUSTOM_EMOJIS["instagram"], "NEW FB": CUSTOM_EMOJIS["facebook"]}
    service_icon_id = svc_emojis.get(svc_name.upper(), CUSTOM_EMOJIS["phone"])
    globe_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["globe"]}">🌐</tg-emoji>'
    text = f"{globe_tag} <b>Country :</b> {flag} {c_name}\n{wait_tag} <i>Waiting for OTP</i>"
    builder = InlineKeyboardBuilder()
    for num in new_nums:
        builder.row(InlineKeyboardButton(text=f" {num}", copy_text=CopyTextButton(text=str(num)), icon_custom_emoji_id=service_icon_id))
    builder.row(InlineKeyboardButton(text="Change Number", callback_data=f"man_change_{svc_id}", icon_custom_emoji_id=CUSTOM_EMOJIS["next"]))
    builder.row(InlineKeyboardButton(text="Change Country", callback_data=f"view_svc_{svc_name}", icon_custom_emoji_id=CUSTOM_EMOJIS["globe"]))
    builder.row(InlineKeyboardButton(text="Home", callback_data="back_to_home", icon_custom_emoji_id=CUSTOM_EMOJIS["store"]),
                InlineKeyboardButton(text="OTP Group ", url=OTP_GROUP_LINK, icon_custom_emoji_id=CUSTOM_EMOJIS["chat"]))
    await safe_edit_message(fetching_msg, text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer("নাম্বার সফলভাবে পরিবর্তন হয়েছে!")

# ---------- Range Number Handlers ----------
RANGE_PATTERN = re.compile(r'[\+]?(\d{5,12}[Xx]{2,5})')

def extract_range_from_text(text: str) -> str:
    match = RANGE_PATTERN.search(text)
    if match:
        range_val = match.group(1).upper().replace('X', 'X')
        if range_val.startswith('+'):
            range_val = range_val[1:]
        return range_val
    return None

@dp.callback_query(F.data == "enter_range")
async def enter_range_prompt(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if await check_maintenance(callback.from_user.id, callback=callback):
        return
    add_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["add"]}">✏️</tg-emoji>'
    await safe_edit_message(callback.message, f"{add_tag} দয়া করে রেঞ্জ লিখুন (যেমন: 99298XXX, 88017XXXXX):")
    await state.set_state(UserStates.waiting_for_range)
    await callback.answer()

@dp.message(UserStates.waiting_for_range)
async def process_entered_range(message: types.Message, state: FSMContext):
    await state.clear()
    await auto_detect_range(message, state)

@dp.message()
async def auto_detect_range(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        return
    if message.text and message.text.startswith('/'):
        return
    if message.text in ["GET NUMBER", "ADMIN PANEL", "GET 2FA", "EXTRACT OTP", "STATUS"]:
        return
    text_to_check = message.text or message.caption or ""
    if not text_to_check:
        return
    if await check_maintenance(message.from_user.id, message=message):
        return
    range_val = extract_range_from_text(text_to_check)
    if not range_val:
        return
    try:
        await message.delete()
    except:
        pass
    await send_range_numbers_message(message, range_val, limit=3)

async def send_range_numbers_message(callback_or_msg, range_val: str, limit: int = 3):
    wait_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["waiting"]}">⏳</tg-emoji>'
    err_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["error"]}">❌</tg-emoji>'
    globe_tag = f'<tg-emoji emoji-id="{CUSTOM_EMOJIS["globe"]}">🌐</tg-emoji>'

    if isinstance(callback_or_msg, types.CallbackQuery):
        target_message = callback_or_msg.message
        await safe_edit_message(target_message, f"{wait_tag} <b>Fetching numbers, please wait...</b>", parse_mode="HTML")
        user_id = callback_or_msg.from_user.id
    else:
        target_message = await safe_send_message(callback_or_msg, f"{wait_tag} <b>Fetching numbers, please wait...</b>", parse_mode="HTML")
        user_id = callback_or_msg.chat.id

    numbers = []
    if FASTX_API_KEY:
        for _ in range(3):
            needed = limit - len(numbers)
            if needed <= 0:
                break
            for _ in range(needed):
                fastx_num, _ = await fastx_get_number(range_val)
                if fastx_num:
                    clean = fastx_num.replace("+", "").replace(" ", "")
                    if not any(phone == clean for _, phone, _ in numbers):
                        numbers.append((None, clean, "FASTX"))
            await asyncio.sleep(1)

    if not numbers:
        try:
            await safe_edit_message(target_message, f"{err_tag} Could not fetch numbers at this moment. Please try again later.", parse_mode="HTML")
        except:
            pass
        return None

    country_code, flag_emoji = get_country_from_phone(numbers[0][1])
    country_name = get_country_name(country_code)
    flag_display = get_custom_flag_emoji(country_code)
    text = f"{globe_tag} <b>Country :</b> {flag_display} {country_name}\n{wait_tag} <i>Waiting for OTP</i>"

    builder = InlineKeyboardBuilder()
    row = cursor.execute("SELECT name FROM services WHERE range_val=?", (range_val,)).fetchone()
    svc_name = row[0] if row else "FACEBOOK"
    svc_emojis = {"FACEBOOK": CUSTOM_EMOJIS["facebook"], "WHATSAPP": CUSTOM_EMOJIS["whatsapp"],
                  "INSTAGRAM": CUSTOM_EMOJIS["instagram"], "NEW FB": CUSTOM_EMOJIS["facebook"]}
    service_icon_id = svc_emojis.get(svc_name.upper(), CUSTOM_EMOJIS["phone"])
    for nid, phone, engine_id in numbers:
        display_phone = format_number_with_plus(phone)
        builder.row(InlineKeyboardButton(text=f" {display_phone}", copy_text=CopyTextButton(text=phone), icon_custom_emoji_id=service_icon_id))
    builder.row(InlineKeyboardButton(text="Change Number", callback_data=f"chg_range_{range_val}_{limit}", icon_custom_emoji_id=CUSTOM_EMOJIS["next"]))
    builder.row(InlineKeyboardButton(text="Change Country", callback_data=f"view_svc_{svc_name}", icon_custom_emoji_id=CUSTOM_EMOJIS["globe"]))
    builder.row(
        InlineKeyboardButton(text="Home", callback_data="back_to_home", icon_custom_emoji_id=CUSTOM_EMOJIS["store"]),
        InlineKeyboardButton(text="OTP Group ", url=OTP_GROUP_LINK, icon_custom_emoji_id=CUSTOM_EMOJIS["chat"])
    )
    try:
        sent = await safe_edit_message(target_message, text, reply_markup=builder.as_markup(), parse_mode="HTML")
    except Exception:
        try:
            await target_message.delete()
        except:
            pass
        if isinstance(callback_or_msg, types.CallbackQuery):
            sent = await safe_send_message(callback_or_msg.message, text, reply_markup=builder.as_markup(), parse_mode="HTML")
        else:
            sent = await safe_send_message(callback_or_msg, text, reply_markup=builder.as_markup(), parse_mode="HTML")
    if isinstance(callback_or_msg, types.Message):
        try:
            await callback_or_msg.delete()
        except:
            pass

    # পেন্ডিং লিস্টে যোগ
    svc_name = row[0] if row else "FACEBOOK"
    for _, phone, _ in numbers:
        pending_otps[phone] = {
            "user_id": user_id,
            "range_val": range_val,
            "service_name": svc_name,
            "start_time": time.time()
        }
    return sent

@dp.callback_query(F.data.startswith("chg_range_"))
async def change_range_number_panel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if await check_maintenance(callback.from_user.id, callback=callback):
        return
    parts = callback.data.split("_")
    await send_range_numbers_message(callback, parts[2], limit=int(parts[3]))

# ================= STARTUP =================
async def on_startup():
    asyncio.create_task(process_manual_expiry())
    asyncio.create_task(fastx_liveaccess_updater())
    asyncio.create_task(live_console_poller())
    asyncio.create_task(success_otp_checker())
    asyncio.create_task(pending_expiry())

dp.startup.register(on_startup)

async def on_shutdown():
    pass

dp.shutdown.register(on_shutdown)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

