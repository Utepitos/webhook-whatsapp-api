from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class UserProfile:
    """Perfil del ciudadano construido durante la conversación."""
    edad: int | None = None
    sexo: str | None = None
    municipio: str | None = None
    departamento: str | None = None
    es_mujer_cabeza_hogar: bool | None = None
    num_personas_hogar: int | None = None
    num_menores_hogar: int | None = None
    num_adultos_mayores_hogar: int | None = None
    tiene_miembro_discapacidad: bool | None = None
    es_victima_conflicto: bool | None = None
    situacion_laboral: str | None = None  # "formal", "informal", "desempleado", "inactivo"
    ingreso_mensual_aprox: int | None = None
    material_paredes: str | None = None
    material_piso: str | None = None
    material_techo: str | None = None
    acceso_agua_potable: bool | None = None
    acceso_alcantarillado: bool | None = None
    acceso_energia: bool | None = None
    tenencia_vivienda: str | None = None  # "propia", "arrendada", "prestada", "invasion"
    nivel_educativo: str | None = None
    tiene_ninos_escolarizados: bool | None = None
    jovenes_quieren_estudiar: bool | None = None
    sisben_actual: str | None = None  # Grupo actual si ya lo saben
    imagen_vivienda_analizada: bool | None = None
    analisis_imagen: str | None = None


@dataclass
class Session:
    user_id: str
    profile: UserProfile = field(default_factory=UserProfile)
    history: list[dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    sisben_aproximado: str | None = None
    beneficios_identificados: list[str] = field(default_factory=list)

    def add_message(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})
        self.last_activity = datetime.now()

    def get_recent_history(self, n: int = 10) -> list[dict]:
        return self.history[-n:]


_sessions: dict[str, Session] = {}


def get_session(user_id: str) -> Session:
    if user_id not in _sessions:
        _sessions[user_id] = Session(user_id=user_id)
    return _sessions[user_id]


def delete_session(user_id: str) -> None:
    _sessions.pop(user_id, None)
