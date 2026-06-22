import streamlit as st
import time
from google import genai
from google.genai import types

st.set_page_config(
    page_title="AI Básník & Spisovatelský Stůl",
    page_icon="✍️",
    layout="centered"
)

# Pomocný styl pro hezčí písmo v editoru poezie
st.markdown("""
    <style>
    .stTextArea textarea {
        font-family: 'Courier New', Courier, monospace;
        font-size: 16px;
        line-height: 1.5;
        background-color: #fcfbf9;
    }
    </style>
""", unsafe_allow_html=True)

if "poem_text" not in st.session_state:
    st.session_state["poem_text"] = ""

st.sidebar.title("🔑 Nastavení")
api_key_input = st.sidebar.text_input(
    "Vlož svůj Gemini API klíč:",
    type="password",
    help="Pokud máš klíč nastavený v systému jako proměnnou prostředí, můžeš toto pole nechat prázdné."
)

# Volba modelu pro obcházení přetížení serverů
model_selection = st.sidebar.selectbox(
    "Vyber model Gemini:",
    [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite"
    ],
    index=0,
    help="Pokud má hlavní model '2.5-flash' výpadky nebo hlásí přetížení (503), přepni na odlehčený '2.5-flash-lite', který je ultra rychlý a mnohem stabilnější."
)

# Inicializace klienta
if api_key_input:
    client = genai.Client(api_key=api_key_input)
else: 
    try:
        client = genai.Client()
    except Exception:
        client = None

def zavolej_gemini_bezpecne(func, *args, **kwargs):
    """
    Spustí funkci pro volání Gemini API. Pokud server vrátí chybu přetížení (503/429),
    automaticky pokus opakuje (až 5x) s postupně se zvyšující pauzou.
    """
    max_retries = 5
    delay = 1.0  # První pauza bude 1 sekunda
    
    for pokus in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            chybova_zprava = str(e)
            je_docasna_chyba = (
                "503" in chybova_zprava or 
                "UNAVAILABLE" in chybova_zprava or 
                "429" in chybova_zprava or 
                "ResourceExhausted" in chybova_zprava
            )
            
            if je_docasna_chyba and pokus < max_retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            else:
                raise e

def generuj_novou_basen(tema, styl, kreativita, model_name):
    if not client:
        return "Chyba: Chybí API klíč. Zadej ho prosím v levém panelu!"
        
    konfigurace = types.GenerateContentConfig(
        system_instruction=(
            "Jsi elitní český básník, mistr hlubokých metafor a silné atmosféry. "
            "Tvé básně mají pevný rým a stabilní rytmus. Nepoužívej laciná klišé "
            "(jako noc/moc, svět/květ, den/sen). Piš originálně a dbej na to, "
            "aby verše měly podobný počet slabik."
        ),
        temperature=kreativita
    )
    
    prompt = f"Napiš báseň na téma '{tema}'. Styl a nálada básně musí být: {styl}."
    
    odpoved = zavolej_gemini_bezpecne(
        client.models.generate_content,
        model=model_name,
        contents=prompt,
        config=konfigurace
    )
    return odpoved.text

def vylepsi_vlastni_verse(vlastni_text, kreativita, model_name):
    if not client:
        return "Chyba: Chybí API klíč. Zadej ho prosím v levém panelu!"
        
    konfigurace = types.GenerateContentConfig(
        system_instruction=(
            "Jsi geniální český básník, editor a citlivý mentor. Uživatel ti pošle své "
            "vlastní verše. Tvým úkolem NENÍ vymyslet novou báseň, ale vzít jeho "
            "surové myšlenky a přepsat je tak, aby měly dokonalý rým a rytmus. "
            "ZACHOVEJ původní atmosféru, melancholii a hlavní pointu."
        ),
        temperature=kreativita
    )
    
    prompt = f"Zde jsou mé osobní verše. Oprav jejich rytmus a rým, ale zachovej emoci:\n\n{vlastni_text}"
    
    odpoved = zavolej_gemini_bezpecne(
        client.models.generate_content,
        model=model_name,
        contents=prompt,
        config=konfigurace
    )
    return odpoved.text

def uprav_basen_podle_instrukce(aktualni_text, instrukce, model_name, kreativita=0.7):
    if not client:
        return "Chyba: Chybí API klíč!"
        
    konfigurace = types.GenerateContentConfig(
        system_instruction=(
            "Jsi elitní básnický editor. Uživatel ti posílá rozepsanou verzi básně, "
            "kterou sám upravuje, a specifickou instrukci, co v ní změnit, přidat nebo opravit. "
            "Proveď požadovanou úpravu extrémně citlivě. Měň pouze to, o co tě uživatel žádá, "
            "a zbytek jeho textu zachovej. Dbej na rytmus a rým."
        ),
        temperature=kreativita
    )
    
    prompt = (
        f"Zde je aktuální verze básně:\n"
        f"---\n{aktualni_text}\n---\n\n"
        f"Uživatel si přeje tuto změnu: {instrukce}"
    )
    
    odpoved = zavolej_gemini_bezpecne(
        client.models.generate_content,
        model=model_name,
        contents=prompt,
        config=konfigurace
    )
    return odpoved.text

st.title("✍️ Tvůj osobní AI Básnický Salon")
st.write("Propoj své lidské pocity s řemeslnou přesností umělé inteligence.")

if not client:
    st.info("💡 Pro začátek prosím vlož svůj API klíč do pole v levém bočním panelu.")

# Vytvoření záložek (tabs)
tab1, tab2 = st.tabs(["✨ Generátor nových básní", "🩹 Ladič mých vlastních veršů"])

# --- ZÁLOŽKA 1: GENERÁTOR ---
with tab1:
    st.subheader("Nech si napsat novou báseň na přání")
    
    tema = st.text_input(
        "O čem má básnička být?", 
        placeholder="Např. Káva v deštivém odpoledni, osamělý maják...",
        key="generator_tema"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        styl = st.selectbox(
            "Styl a nálada:",
            [
                "Klasická rýmovaná (melancholická)", 
                "Veselá a hravá s humorem", 
                "Temná gothická balada", 
                "Tradiční japonské Haiku", 
                "Moderní volný verš (bez rýmů)"
            ]
        )
    with col2:
        kreativita = st.slider(
            "Míra fantazie (Temperature):", 
            min_value=0.1, 
            max_value=1.0, 
            value=0.85, 
            step=0.05,
            key="generator_kreativita"
        )
        
    if st.button("Složit novou báseň ✨", use_container_width=True):
        if not tema:
            st.warning("Nejdříve zadej téma básně!")
        elif not client:
            st.error("Zadej prosím API klíč v levém panelu!")
        else:
            with st.spinner("AI hledá ta správná slova..."):
                try:
                    vysledek = generuj_novou_basen(tema, styl, kreativita, model_selection)
                    st.session_state["poem_text"] = vysledek
                    st.rerun()
                except Exception as e:
                    st.error(
                        "⚠️ Servery Googlu jsou momentálně přetížené a neodpověděly ani po několika pokusech. "
                        "Zkus v levém panelu přepnout na stabilnější odlehčený model 'gemini-2.5-flash-lite'! "
                        f"(Detaily: {e})"
                    )

# --- ZÁLOŽKA 2: LADIČ VERŠŮ ---
with tab2:
    st.subheader("Dej svým vlastním emocím dokonalý rytmus")
    st.write(
        "Napiš sem své myšlenky, věty nebo syrové pocity. "
        "AI je přepíše do vybroušené básnické podoby, aniž by ztratila tvou duši."
    )
    
    vlastni_text = st.text_area(
        "Vlož své surové verše nebo pocity:",
        placeholder=(
            "Příklad:\n"
            "Nemůžu na ni přestat myslet,\n"
            "je jako krásný sen...\n"
            "Já jsem jen pěšák, ona princezna..."
        ),
        height=180,
        key="vlastni_surovy_text"
    )
    
    kreativita_ladic = st.slider(
        "Míra básnické volnosti:", 
        min_value=0.1, 
        max_value=1.0, 
        value=0.7, 
        step=0.05,
        key="ladic_kreativita"
    )
    
    if st.button("Vylepšit a poslat do editoru 🩹", use_container_width=True):
        if not vlastni_text:
            st.warning("Nejdříve sem napiš nebo vlož nějaké své verše!")
        elif not client:
            st.error("Zadej prosím API klíč v levém panelu!")
        else:
            with st.spinner("AI citlivě ladí rytmus tvých veršů..."):
                try:
                    vysledek = vylepsi_vlastni_verse(vlastni_text, kreativita_ladic, model_selection)
                    st.session_state["poem_text"] = vysledek
                    st.rerun()
                except Exception as e:
                    st.error(
                        "⚠️ Servery Googlu jsou momentálně přetížené a neodpověděly ani po několika pokusech. "
                        "Zkus v levém panelu přepnout na stabilnější odlehčený model 'gemini-2.5-flash-lite'! "
                        f"(Detaily: {e})"
                    )

# --- SPOLEČNÝ BÁSNICKÝ PRACOVNÍ STŮL ---
if st.session_state.get("poem_text"):
    st.markdown("---")
    st.subheader("📝 Tvůj kreativní pracovní stůl")
    st.info("💡 Klikni do textového pole níže a můžeš báseň přímo ručně přepisovat, upravovat a dopisovat!")
    
    # Text area je propojená s pamětí.
    edited_poem = st.text_area(
        "Aktuální rozpracovaná verze básně:",
        value=st.session_state.get("poem_text", ""),
        height=400,
        key="poem_editor"
    )
    
    st.session_state["poem_text"] = edited_poem
    
    st.markdown("### 🤖 Nechat AI provést další úpravu")
    st.write("Můžeš AI říct, co přesně má s tvou aktuální verzí nahoře udělat.")
    
    instrukce = st.text_input(
        "Napiš instrukci pro AI:",
        placeholder="Např. 'Změň třetí sloku, ať je víc optimistická' nebo 'Zkrať celou báseň na polovinu'...",
        key="ai_edit_instruction"
    )
    
    if st.button("Upravit podle instrukce 🪄", use_container_width=True):
        if not instrukce:
            st.warning("Napiš nejdříve instrukci, co má AI změnit!")
        elif not client:
            st.error("Zadej prosím API klíč!")
        else:
            with st.spinner("AI provádí úpravy tvé básně..."):
                try:
                    upraveny_vysledek = uprav_basen_podle_instrukce(
                        st.session_state.get("poem_text", ""), 
                        instrukce,
                        model_selection
                    )
                    st.session_state["poem_text"] = upraveny_vysledek
                    st.rerun()
                except Exception as e:
                    st.error(
                        "⚠️ Servery Googlu jsou momentálně přetížené a neodpověděly ani po několika pokusech. "
                        "Zkus v levém panelu přepnout na stabilnější odlehčený model 'gemini-2.5-flash-lite'! "
                        f"(Detaily: {e})"
                    )