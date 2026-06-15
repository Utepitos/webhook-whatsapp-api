from app.agent.session import UserProfile
from app.constants import (
    SISBEN_INITIAL_SCORE,
    SISBEN_SCORE_FLOOR,
    SISBEN_SCORE_CEILING,
    SISBEN_GROUP_A_MAX,
    SISBEN_GROUP_B_MAX,
    SISBEN_GROUP_C_MAX,
)

# Tipo alias para legibilidad
_ScoreDelta = tuple[float, list[str]]


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(k in text for k in keywords)


def _score_housing(profile: UserProfile) -> _ScoreDelta:
    """Evalúa condiciones de la vivienda: piso, paredes y techo."""
    delta = 0.0
    reasons: list[str] = []

    if profile.material_piso:
        piso = profile.material_piso.lower()
        if _contains_any(piso, ["tierra", "arena"]):
            delta -= 20; reasons.append("piso de tierra (-)")
        elif _contains_any(piso, ["cemento", "madera"]):
            delta -= 5; reasons.append("piso básico (-)")
        elif _contains_any(piso, ["baldosa", "cerámica", "vinilo"]):
            delta += 5; reasons.append("piso adecuado (+)")

    if profile.material_paredes:
        paredes = profile.material_paredes.lower()
        if _contains_any(paredes, ["zinc", "cartón", "plástico", "tela", "bahareque"]):
            delta -= 18; reasons.append("paredes precarias (-)")
        elif _contains_any(paredes, ["madera", "adobe", "tapia"]):
            delta -= 10; reasons.append("paredes de madera o adobe (-)")
        elif _contains_any(paredes, ["bloque", "ladrillo"]):
            delta += 3; reasons.append("paredes sólidas (+)")

    if profile.material_techo:
        techo = profile.material_techo.lower()
        if _contains_any(techo, ["paja", "palma", "plástico", "cartón"]):
            delta -= 15; reasons.append("techo precario (-)")
        elif "zinc" in techo:
            delta -= 5; reasons.append("techo de zinc (-)")
        elif _contains_any(techo, ["losa", "concreto"]):
            delta += 5; reasons.append("techo de losa (+)")

    if profile.tenencia_vivienda == "invasion":
        delta -= 10; reasons.append("vivienda en invasión (-)")
    elif profile.tenencia_vivienda == "propia":
        delta += 5; reasons.append("vivienda propia (+)")

    return delta, reasons


def _score_services(profile: UserProfile) -> _ScoreDelta:
    """Evalúa acceso a servicios públicos domiciliarios."""
    delta = 0.0
    reasons: list[str] = []

    if profile.acceso_agua_potable is False:
        delta -= 15; reasons.append("sin agua potable (-)")
    elif profile.acceso_agua_potable is True:
        delta += 5; reasons.append("agua potable (+)")

    if profile.acceso_alcantarillado is False:
        delta -= 10; reasons.append("sin alcantarillado (-)")
    elif profile.acceso_alcantarillado is True:
        delta += 3; reasons.append("alcantarillado (+)")

    if profile.acceso_energia is False:
        delta -= 10; reasons.append("sin energía eléctrica (-)")

    return delta, reasons


def _score_household_composition(profile: UserProfile) -> _ScoreDelta:
    """Evalúa la composición y vulnerabilidades del hogar."""
    delta = 0.0
    reasons: list[str] = []

    if profile.es_mujer_cabeza_hogar:
        delta -= 5; reasons.append("mujer cabeza de hogar (-)")

    if profile.tiene_miembro_discapacidad:
        delta -= 5; reasons.append("miembro con discapacidad (-)")

    if profile.es_victima_conflicto:
        delta -= 8; reasons.append("víctima del conflicto (-)")

    has_overcrowding = profile.num_personas_hogar and profile.num_personas_hogar >= 6
    if has_overcrowding:
        delta -= 8; reasons.append("posible hacinamiento (-)")

    has_high_minor_ratio = (
        profile.num_menores_hogar
        and profile.num_personas_hogar
        and (profile.num_menores_hogar / profile.num_personas_hogar) > 0.5
    )
    if has_high_minor_ratio:
        delta -= 8; reasons.append("hogar con muchos menores (-)")

    return delta, reasons


def _score_employment_and_income(profile: UserProfile) -> _ScoreDelta:
    """Evalúa situación laboral, ingresos y nivel educativo del jefe de hogar."""
    delta = 0.0
    reasons: list[str] = []

    if profile.situacion_laboral:
        lab = profile.situacion_laboral.lower()
        if "desempleado" in lab:
            delta -= 12; reasons.append("sin empleo (-)")
        elif "informal" in lab:
            delta -= 6; reasons.append("empleo informal (-)")
        elif "formal" in lab:
            delta += 8; reasons.append("empleo formal (+)")

    if profile.ingreso_mensual_aprox is not None:
        ingreso = profile.ingreso_mensual_aprox
        if ingreso < 200_000:
            delta -= 15; reasons.append("ingreso muy bajo (-)")
        elif ingreso < 500_000:
            delta -= 8; reasons.append("ingreso bajo (-)")
        elif ingreso < 1_300_000:
            delta += 2
        else:
            delta += 10; reasons.append("ingreso medio o alto (+)")

    if profile.nivel_educativo:
        edu = profile.nivel_educativo.lower()
        if _contains_any(edu, ["ninguno", "primaria"]):
            delta -= 5; reasons.append("bajo nivel educativo (-)")
        elif _contains_any(edu, ["técnica", "tecnológica"]):
            delta += 5; reasons.append("educación técnica (+)")
        elif _contains_any(edu, ["universitaria", "profesional"]):
            delta += 10; reasons.append("educación universitaria (+)")

    return delta, reasons


def _group_from_score(score: float) -> str:
    if score <= SISBEN_GROUP_A_MAX:
        return "A"
    if score <= SISBEN_GROUP_B_MAX:
        return "B"
    if score <= SISBEN_GROUP_C_MAX:
        return "C"
    return "D"


def aproximar_grupo_sisben(profile: UserProfile) -> tuple[str, str]:
    """
    Aproximación del grupo SISBEN IV a partir del perfil recopilado.
    Retorna (grupo, justificacion).

    NOTA: Orientativa. El puntaje oficial lo determina el DANE
    mediante encuesta presencial.
    """
    scoring_functions = [
        _score_housing,
        _score_services,
        _score_household_composition,
        _score_employment_and_income,
    ]

    total_delta = 0.0
    all_reasons: list[str] = []

    for score_fn in scoring_functions:
        delta, reasons = score_fn(profile)
        total_delta += delta
        all_reasons.extend(reasons)

    score = max(SISBEN_SCORE_FLOOR, min(SISBEN_SCORE_CEILING, SISBEN_INITIAL_SCORE + total_delta))
    grupo = _group_from_score(score)
    factors = ", ".join(all_reasons) if all_reasons else "perfil estándar"
    justificacion = f"Puntaje estimado: {score:.1f}. Factores: {factors}"

    return grupo, justificacion
