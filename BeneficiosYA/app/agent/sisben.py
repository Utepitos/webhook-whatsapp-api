from app.agent.session import UserProfile


def aproximar_grupo_sisben(profile: UserProfile) -> tuple[str, str]:
    """
    Aproximación del grupo SISBEN IV basada en el perfil recopilado.
    Retorna (grupo, justificacion).

    NOTA: Esta es una aproximación orientativa. El puntaje real lo determina
    el DANE mediante encuesta presencial oficial.
    """
    score = 50.0  # Puntaje base (punto medio del rango C)
    justificacion = []

    # --- Vivienda (impacto alto) ---
    if profile.material_piso:
        piso = profile.material_piso.lower()
        if "tierra" in piso or "arena" in piso:
            score -= 20
            justificacion.append("piso de tierra (-)")
        elif "cemento" in piso or "madera" in piso:
            score -= 5
            justificacion.append("piso básico (-)")
        elif "baldosa" in piso or "cerámica" in piso or "vinilo" in piso:
            score += 5
            justificacion.append("piso adecuado (+)")

    if profile.material_paredes:
        paredes = profile.material_paredes.lower()
        if any(m in paredes for m in ["zinc", "cartón", "plástico", "tela", "bahareque"]):
            score -= 18
            justificacion.append("paredes de material precario (-)")
        elif any(m in paredes for m in ["madera", "adobe", "tapia"]):
            score -= 10
            justificacion.append("paredes de madera o adobe (-)")
        elif "bloque" in paredes or "ladrillo" in paredes:
            score += 3
            justificacion.append("paredes de bloque o ladrillo (+)")

    if profile.material_techo:
        techo = profile.material_techo.lower()
        if any(m in techo for m in ["paja", "palma", "plástico", "cartón"]):
            score -= 15
            justificacion.append("techo de material precario (-)")
        elif "zinc" in techo:
            score -= 5
            justificacion.append("techo de zinc (-)")
        elif "losa" in techo or "concreto" in techo:
            score += 5
            justificacion.append("techo de losa (+)")

    # --- Servicios (impacto alto) ---
    if profile.acceso_agua_potable is False:
        score -= 15
        justificacion.append("sin agua potable (-)")
    elif profile.acceso_agua_potable is True:
        score += 5
        justificacion.append("con agua potable (+)")

    if profile.acceso_alcantarillado is False:
        score -= 10
        justificacion.append("sin alcantarillado (-)")
    elif profile.acceso_alcantarillado is True:
        score += 3
        justificacion.append("con alcantarillado (+)")

    if profile.acceso_energia is False:
        score -= 10
        justificacion.append("sin energía eléctrica (-)")

    # --- Composición del hogar (impacto medio) ---
    if profile.es_mujer_cabeza_hogar:
        score -= 5
        justificacion.append("mujer cabeza de hogar (-)")

    if profile.num_menores_hogar and profile.num_personas_hogar:
        ratio_menores = profile.num_menores_hogar / profile.num_personas_hogar
        if ratio_menores > 0.5:
            score -= 8
            justificacion.append("hogar con muchos menores (-)")

    if profile.tiene_miembro_discapacidad:
        score -= 5
        justificacion.append("miembro con discapacidad (-)")

    if profile.es_victima_conflicto:
        score -= 8
        justificacion.append("víctima del conflicto (-)")

    # --- Hacinamiento ---
    if profile.num_personas_hogar and profile.num_personas_hogar >= 6:
        score -= 8
        justificacion.append("posible hacinamiento (-)")

    # --- Ingresos y empleo (impacto alto) ---
    if profile.situacion_laboral:
        lab = profile.situacion_laboral.lower()
        if "desempleado" in lab:
            score -= 12
            justificacion.append("sin empleo (-)")
        elif "informal" in lab:
            score -= 6
            justificacion.append("empleo informal (-)")
        elif "formal" in lab:
            score += 8
            justificacion.append("empleo formal (+)")

    if profile.ingreso_mensual_aprox:
        ingreso = profile.ingreso_mensual_aprox
        if ingreso < 200_000:
            score -= 15
            justificacion.append("ingreso muy bajo (-)")
        elif ingreso < 500_000:
            score -= 8
            justificacion.append("ingreso bajo (-)")
        elif ingreso < 1_300_000:
            score += 2
        else:
            score += 10
            justificacion.append("ingreso medio o alto (+)")

    # --- Vivienda en invasión ---
    if profile.tenencia_vivienda == "invasion":
        score -= 10
        justificacion.append("vivienda en invasión (-)")
    elif profile.tenencia_vivienda == "propia":
        score += 5
        justificacion.append("vivienda propia (+)")

    # --- Educación jefe hogar (impacto medio) ---
    if profile.nivel_educativo:
        edu = profile.nivel_educativo.lower()
        if "ninguno" in edu or "primaria" in edu:
            score -= 5
            justificacion.append("bajo nivel educativo (-)")
        elif "técnica" in edu or "tecnológica" in edu:
            score += 5
            justificacion.append("educación técnica (+)")
        elif "universitaria" in edu or "profesional" in edu:
            score += 10
            justificacion.append("educación universitaria (+)")

    # Asegurar rango razonable
    score = max(0, min(80, score))

    if score <= 11.68:
        grupo = "A"
    elif score <= 22.89:
        grupo = "B"
    elif score <= 47.99:
        grupo = "C"
    else:
        grupo = "D"

    return grupo, f"Puntaje estimado: {score:.1f}. Factores: {', '.join(justificacion) if justificacion else 'perfil estándar'}"
