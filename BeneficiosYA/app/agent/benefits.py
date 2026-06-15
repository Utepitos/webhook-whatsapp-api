import json
from pathlib import Path
from app.agent.session import UserProfile

_benefits_cache: list[dict] | None = None


def _load_benefits() -> list[dict]:
    global _benefits_cache
    if _benefits_cache is None:
        path = Path(__file__).parent.parent / "data" / "benefits.json"
        _benefits_cache = json.loads(path.read_text(encoding="utf-8"))
    return _benefits_cache


def match_benefits(profile: UserProfile, sisben_grupo: str) -> list[dict]:
    """Retorna la lista de beneficios relevantes para el perfil dado."""
    benefits = _load_benefits()
    matched = []
    grupo = sisben_grupo.upper()

    for benefit in benefits:
        sisben_requerido = benefit.get("sisben_grupos", [])
        aplica_para = benefit.get("aplica_para", [])

        # Filtro por grupo SISBEN
        if sisben_requerido and grupo not in sisben_requerido:
            continue

        # Filtros adicionales por perfil
        if "adulto_mayor" in aplica_para:
            if not profile.num_adultos_mayores_hogar:
                edad_aplica = profile.edad and profile.edad >= 55
                if not edad_aplica:
                    continue

        if "gestantes" in aplica_para and not profile.es_mujer_cabeza_hogar:
            pass

        if "victimas_conflicto" in aplica_para and not profile.es_victima_conflicto:
            if "todos_sisben" not in aplica_para:
                continue

        if "discapacidad" in aplica_para and not profile.tiene_miembro_discapacidad:
            if "todos_sisben" not in aplica_para:
                continue

        matched.append(benefit)

    return matched


def format_benefits_summary(benefits: list[dict]) -> str:
    """Formatea el listado de beneficios para incluir en el contexto del agente."""
    if not benefits:
        return "No se encontraron beneficios específicos para este perfil."

    lines = [f"BENEFICIOS IDENTIFICADOS ({len(benefits)} programas):"]
    for i, b in enumerate(benefits, 1):
        lines.append(f"\n{i}. {b['nombre']} ({b['entidad']})")
        lines.append(f"   {b['descripcion']}")
        montos = b.get("beneficio", {}).get("montos", {})
        if montos:
            for k, v in list(montos.items())[:2]:
                lines.append(f"   → {v}")
        lines.append(f"   Contacto: {b.get('contacto', 'Ver sitio web')}")

    return "\n".join(lines)
