import pytest
from app.agent.session import UserProfile
from app.agent.benefits import match_benefits, format_benefits_summary


def make_profile(**kwargs) -> UserProfile:
    p = UserProfile()
    for k, v in kwargs.items():
        setattr(p, k, v)
    return p


class TestBenefitsMatching:

    def test_sisben_A_incluye_familias_en_accion(self):
        profile = make_profile(num_menores_hogar=2)
        benefits = match_benefits(profile, "A")
        ids = [b["id"] for b in benefits]
        assert "familias_en_accion" in ids

    def test_sisben_D_excluye_familias_en_accion(self):
        profile = make_profile()
        benefits = match_benefits(profile, "D")
        ids = [b["id"] for b in benefits]
        assert "familias_en_accion" not in ids

    def test_sisben_A_incluye_regimen_subsidiado(self):
        profile = make_profile()
        benefits = match_benefits(profile, "A")
        ids = [b["id"] for b in benefits]
        assert "regimen_subsidiado_salud" in ids

    def test_sisben_C_incluye_matricula_cero(self):
        profile = make_profile()
        benefits = match_benefits(profile, "C")
        ids = [b["id"] for b in benefits]
        assert "matricula_cero" in ids

    def test_sisben_A_incluye_colombia_mayor_con_adulto_mayor(self):
        profile = make_profile(num_adultos_mayores_hogar=1)
        benefits = match_benefits(profile, "A")
        ids = [b["id"] for b in benefits]
        assert "colombia_mayor" in ids

    def test_victimas_conflicto_incluye_beneficio_victimas(self):
        profile = make_profile(es_victima_conflicto=True)
        benefits = match_benefits(profile, "B")
        ids = [b["id"] for b in benefits]
        assert "victimas_conflicto" in ids

    def test_sena_disponible_para_todos_los_grupos(self):
        for grupo in ["A", "B", "C", "D"]:
            profile = make_profile()
            benefits = match_benefits(profile, grupo)
            ids = [b["id"] for b in benefits]
            assert "sena_gratuito" in ids, f"SENA no encontrado para grupo {grupo}"

    def test_resultado_no_vacio_para_sisben_A(self):
        profile = make_profile()
        benefits = match_benefits(profile, "A")
        assert len(benefits) > 0

    def test_formato_summary_contiene_nombre_beneficio(self):
        profile = make_profile()
        benefits = match_benefits(profile, "A")
        summary = format_benefits_summary(benefits)
        assert "Familias en Acción" in summary or "SENA" in summary

    def test_formato_summary_lista_vacia(self):
        summary = format_benefits_summary([])
        assert "No se encontraron" in summary

    def test_jovenes_en_accion_sisben_C(self):
        profile = make_profile()
        benefits = match_benefits(profile, "C")
        ids = [b["id"] for b in benefits]
        assert "jovenes_en_accion" in ids
