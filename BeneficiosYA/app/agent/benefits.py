import json
from functools import lru_cache
from pathlib import Path
from app.agent.session import UserProfile


@lru_cache(maxsize=1)
def _load_benefits() -> tuple[dict, ...]:
    """Carga el catálogo de beneficios una sola vez y lo mantiene inmutable."""
    path = Path(__file__).parent.parent / "data" / "benefits.json"
    return tuple(json.loads(path.read_text(encoding="utf-8")))


def _matches_sisben_group(benefit: dict, grupo: str) -> bool:
    required = benefit.get("sisben_grupos", [])
    return not required or grupo in required


def _matches_special_criteria(benefit: dict, profile: UserProfile) -> bool:
    """Retorna False si el beneficio requiere una característica que el perfil no tiene."""
    tags = set(benefit.get("aplica_para", []))
    is_universal = "todos_sisben" in tags

    if "adulto_mayor" in tags and not is_universal:
        has_elderly_in_home = bool(profile.num_adultos_mayores_hogar)
        user_is_elderly = bool(profile.edad and profile.edad >= 55)
        if not (has_elderly_in_home or user_is_elderly):
            return False

    if "victimas_conflicto" in tags and not is_universal:
        if not profile.es_victima_conflicto:
            return False

    if "discapacidad" in tags and not is_universal:
        if not profile.tiene_miembro_discapacidad:
            return False

    return True


def _is_eligible(benefit: dict, profile: UserProfile, grupo: str) -> bool:
    return (
        _matches_sisben_group(benefit, grupo)
        and _matches_special_criteria(benefit, profile)
    )


def match_benefits(profile: UserProfile, sisben_grupo: str) -> list[dict]:
    """Retorna los beneficios a los que el perfil puede acceder según su grupo SISBEN."""
    grupo = sisben_grupo.upper()
    return [b for b in _load_benefits() if _is_eligible(b, profile, grupo)]


def format_benefits_summary(benefits: list[dict]) -> str:
    """Formatea el listado de beneficios para incluir en el contexto del agente."""
    if not benefits:
        return "No se encontraron beneficios específicos para este perfil."

    lines = [f"BENEFICIOS IDENTIFICADOS ({len(benefits)} programas):"]
    for i, benefit in enumerate(benefits, 1):
        montos = benefit.get("beneficio", {}).get("montos", {})
        monto_lines = [f"   → {v}" for v in list(montos.values())[:2]]
        lines.extend([
            f"\n{i}. {benefit['nombre']} ({benefit['entidad']})",
            f"   {benefit['descripcion']}",
            *monto_lines,
            f"   Contacto: {benefit.get('contacto', 'Ver sitio web')}",
        ])

    return "\n".join(lines)
