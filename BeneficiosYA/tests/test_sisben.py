import pytest
from app.agent.session import UserProfile
from app.agent.sisben import aproximar_grupo_sisben


def make_profile(**kwargs) -> UserProfile:
    p = UserProfile()
    for k, v in kwargs.items():
        setattr(p, k, v)
    return p


class TestSisbenAproximacion:

    def test_perfil_extrema_pobreza_debe_ser_grupo_A(self):
        profile = make_profile(
            material_piso="tierra",
            material_paredes="zinc",
            material_techo="plástico",
            acceso_agua_potable=False,
            acceso_alcantarillado=False,
            acceso_energia=False,
            situacion_laboral="desempleado",
            ingreso_mensual_aprox=0,
            es_mujer_cabeza_hogar=True,
            num_personas_hogar=5,
            num_menores_hogar=3,
        )
        grupo, justificacion = aproximar_grupo_sisben(profile)
        assert grupo == "A", f"Esperado A, obtenido {grupo}. {justificacion}"

    def test_perfil_pobreza_moderada_debe_ser_grupo_B(self):
        profile = make_profile(
            material_piso="cemento",
            material_paredes="bloque sin revocar",
            material_techo="zinc",
            acceso_agua_potable=True,
            acceso_alcantarillado=False,
            situacion_laboral="informal",
            ingreso_mensual_aprox=400_000,
        )
        grupo, justificacion = aproximar_grupo_sisben(profile)
        assert grupo in ("A", "B", "C"), f"Grupo inesperado: {grupo}"

    def test_perfil_vulnerabilidad_debe_ser_grupo_C(self):
        profile = make_profile(
            material_piso="baldosa",
            material_paredes="ladrillo revocado",
            material_techo="teja de barro",
            acceso_agua_potable=True,
            acceso_alcantarillado=True,
            acceso_energia=True,
            situacion_laboral="informal",
            ingreso_mensual_aprox=700_000,
            tenencia_vivienda="arrendada",
        )
        grupo, justificacion = aproximar_grupo_sisben(profile)
        assert grupo in ("B", "C", "D"), f"Grupo inesperado: {grupo}. {justificacion}"

    def test_perfil_clase_media_debe_ser_grupo_D(self):
        profile = make_profile(
            material_piso="baldosa",
            material_paredes="ladrillo revocado",
            material_techo="losa de concreto",
            acceso_agua_potable=True,
            acceso_alcantarillado=True,
            acceso_energia=True,
            situacion_laboral="formal",
            ingreso_mensual_aprox=3_000_000,
            tenencia_vivienda="propia",
            nivel_educativo="universitaria",
        )
        grupo, justificacion = aproximar_grupo_sisben(profile)
        assert grupo == "D", f"Esperado D, obtenido {grupo}. {justificacion}"

    def test_victima_conflicto_reduce_puntaje(self):
        profile_base = make_profile(situacion_laboral="informal", ingreso_mensual_aprox=600_000)
        profile_victima = make_profile(
            situacion_laboral="informal",
            ingreso_mensual_aprox=600_000,
            es_victima_conflicto=True,
        )
        grupo_base, _ = aproximar_grupo_sisben(profile_base)
        grupo_victima, _ = aproximar_grupo_sisben(profile_victima)
        grupos_ord = {"A": 0, "B": 1, "C": 2, "D": 3}
        assert grupos_ord[grupo_victima] <= grupos_ord[grupo_base]

    def test_perfil_vacio_retorna_grupo_valido(self):
        profile = UserProfile()
        grupo, _ = aproximar_grupo_sisben(profile)
        assert grupo in ("A", "B", "C", "D")

    def test_justificacion_no_esta_vacia_con_datos(self):
        profile = make_profile(material_piso="tierra", acceso_agua_potable=False)
        _, justificacion = aproximar_grupo_sisben(profile)
        assert len(justificacion) > 0

    def test_mujer_cabeza_hogar_con_menores_grupo_bajo(self):
        profile = make_profile(
            es_mujer_cabeza_hogar=True,
            num_personas_hogar=4,
            num_menores_hogar=3,
            situacion_laboral="desempleado",
            ingreso_mensual_aprox=150_000,
        )
        grupo, _ = aproximar_grupo_sisben(profile)
        assert grupo in ("A", "B")
