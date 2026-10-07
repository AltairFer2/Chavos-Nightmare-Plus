"""Nombres de las escenas de cámara: cómo se componen y cómo se leen.

Solo se prueba la parte pura (mundo/habitaciones.py), que no toca disco ni
pygame. El catálogo que explora las carpetas se prueba aparte, contra los
assets reales.
"""

import pytest

from vecindad.dominio.animatronicos import (
    ELENCO,
    habitaciones_posibles,
    habitaciones_que_se_dibujan,
    nombres,
    nombres_reconocidos_en_escenas,
    prefijos_por_nombre,
)
from vecindad.mundo.habitaciones import (
    HABITACIONES,
    leer_nombre_de_escena,
    nombre_de_escena,
    normalizar_nombre_corto,
)

VALIDOS = nombres_reconocidos_en_escenas()


class TestComponerNombre:
    def test_un_solo_personaje(self):
        assert nombre_de_escena(["ramon"]) == "ramon"

    def test_dos_personajes_van_unidos_con_y(self):
        assert nombre_de_escena(["ramon", "chavo"]) == "ramon y chavo"

    def test_tres_o_mas_solo_llevan_y_al_final(self):
        assert nombre_de_escena(
            ["ramon", "chilindrina", "chavo"]
        ) == "ramon chilindrina y chavo"

    def test_la_primera_version_no_lleva_numero(self):
        assert nombre_de_escena(["ramon"], variante=1) == "ramon"

    def test_las_demas_versiones_llevan_su_numero(self):
        assert nombre_de_escena(["quico", "chavo"], variante=2) == "quico y chavo 2"

    def test_sin_personajes_no_hay_nombre(self):
        assert nombre_de_escena([]) == ""


class TestLeerNombre:
    def test_lee_un_solo_personaje(self):
        assert leer_nombre_de_escena("ramon", VALIDOS) == (frozenset({"ramon"}), 1)

    def test_lee_un_par(self):
        grupo, version = leer_nombre_de_escena("ramon y chavo", VALIDOS)
        assert grupo == frozenset({"ramon", "chavo"})
        assert version == 1

    def test_lee_un_trio(self):
        grupo, _ = leer_nombre_de_escena("ramon chilindrina y chavo", VALIDOS)
        assert grupo == frozenset({"ramon", "chilindrina", "chavo"})

    def test_lee_la_version(self):
        grupo, version = leer_nombre_de_escena("ramon y chilindrina 2", VALIDOS)
        assert grupo == frozenset({"ramon", "chilindrina"})
        assert version == 2

    def test_el_orden_de_los_nombres_da_igual(self):
        """En los assets conviven 'quico y chavo' y 'chavo quico y florinda',
        así que lo único fiable es quiénes salen, no en qué orden."""
        uno, _ = leer_nombre_de_escena("quico y chavo", VALIDOS)
        otro, _ = leer_nombre_de_escena("chavo y quico", VALIDOS)
        assert uno == otro

    @pytest.mark.parametrize(
        "archivo_base", ["cam 72", "Marco Cam 72", "Cam 72 Selected", "Cam Unselected"]
    )
    def test_los_archivos_base_no_se_confunden_con_escenas(self, archivo_base):
        assert leer_nombre_de_escena(archivo_base, VALIDOS) is None

    def test_un_personaje_inventado_no_es_escena(self):
        assert leer_nombre_de_escena("godinez", VALIDOS) is None

    def test_un_grupo_con_un_desconocido_no_es_escena(self):
        """Si no se reconoce a uno de los que salen, la imagen enseñaría a
        alguien que el juego no sabe que está ahí."""
        assert leer_nombre_de_escena("ramon y godinez", VALIDOS) is None

    def test_un_nombre_repetido_no_es_escena(self):
        assert leer_nombre_de_escena("ramon y ramon", VALIDOS) is None

    def test_un_nombre_vacio_no_es_escena(self):
        assert leer_nombre_de_escena("   ", VALIDOS) is None


class TestTildesYMayusculas:
    """Los assets alternan "ramon" y "ramón", a veces en la misma carpeta."""

    def test_la_tilde_no_cambia_el_personaje(self):
        con, _ = leer_nombre_de_escena("ramón y chilindrina", VALIDOS)
        sin, _ = leer_nombre_de_escena("ramon y chilindrina", VALIDOS)
        assert con == sin

    def test_la_tilde_tampoco_dentro_de_un_trio(self):
        con, _ = leer_nombre_de_escena("chilindrina bruja y ramón", VALIDOS)
        sin, _ = leer_nombre_de_escena("chilindrina bruja y ramon", VALIDOS)
        assert con == sin

    def test_las_mayusculas_dan_igual(self):
        alta, _ = leer_nombre_de_escena("Ramon Y Chavo", VALIDOS)
        baja, _ = leer_nombre_de_escena("ramon y chavo", VALIDOS)
        assert alta == baja

    def test_normalizar_quita_tildes_y_baja_a_minusculas(self):
        assert normalizar_nombre_corto("Ramón") == "ramon"


class TestAlias:
    """A Doña Clotilde los assets la llaman "bruja" y a Jaimico, "jaimito"."""

    @pytest.mark.parametrize(
        "alias,oficial", sorted(nombres.ALIAS_EN_ESCENAS.items())
    )
    def test_cada_alias_lleva_a_su_personaje(self, alias, oficial):
        grupo, _ = leer_nombre_de_escena(alias, VALIDOS)
        assert grupo == frozenset({oficial})

    def test_el_alias_y_el_nombre_oficial_son_el_mismo_grupo(self):
        con_alias, _ = leer_nombre_de_escena("chilindrina y bruja", VALIDOS)
        oficial, _ = leer_nombre_de_escena("chilindrina y clotilde", VALIDOS)
        assert con_alias == oficial

    def test_todos_los_alias_apuntan_a_alguien_del_elenco(self):
        oficiales = set(prefijos_por_nombre().values())
        assert set(nombres.ALIAS_EN_ESCENAS.values()).issubset(oficiales)

    def test_ningun_alias_pisa_un_nombre_oficial(self):
        """Un alias con el mismo texto que otro personaje haría ambiguo el
        archivo: no se sabría a cuál de los dos se refiere."""
        oficiales = set(prefijos_por_nombre().values())
        assert not set(nombres.ALIAS_EN_ESCENAS).intersection(oficiales)


class TestIdaYVuelta:
    @pytest.mark.parametrize(
        "prefijos",
        [
            ["ramon"],
            ["ramon", "chavo"],
            ["ramon", "chilindrina", "chavo"],
            ["florinda", "quico", "chavo", "clotilde"],
        ],
    )
    @pytest.mark.parametrize("version", [1, 2, 7])
    def test_lo_que_se_compone_se_puede_volver_a_leer(self, prefijos, version):
        nombre = nombre_de_escena(prefijos, version)
        grupo, leida = leer_nombre_de_escena(nombre, VALIDOS)
        assert grupo == frozenset(prefijos)
        assert leida == version


class TestPrefijos:
    def test_cada_personaje_tiene_su_nombre_corto(self):
        prefijos = prefijos_por_nombre()
        assert len(prefijos) == len(ELENCO)
        assert all(prefijos.values())

    def test_los_nombres_cortos_no_se_repiten(self):
        """Dos personajes con el mismo prefijo harían ambiguo el nombre de
        archivo de cualquier escena en la que salgan juntos."""
        prefijos = list(prefijos_por_nombre().values())
        assert len(set(prefijos)) == len(prefijos)

    def test_ningun_nombre_corto_lleva_espacios(self):
        """El espacio es el separador dentro del nombre de archivo."""
        assert all(" " not in p for p in prefijos_por_nombre().values())

    def test_ningun_nombre_corto_es_un_numero(self):
        """Se confundiría con el sufijo de versión."""
        assert not any(p.isdigit() for p in prefijos_por_nombre().values())


class TestArteQueNoHaceFalta:
    """Doña Florinda llegando al Primer Patio acaba la noche en el acto, así
    que su imagen ahí no se vería nunca y no tiene sentido pedirla."""

    def test_la_llegada_mortal_no_pide_arte_en_el_patio(self):
        dibujables = habitaciones_que_se_dibujan()["primer_patio"]
        assert nombres.FLORINDA not in dibujables

    def test_pero_sigue_pudiendo_estar_ahi(self):
        """La regla es solo sobre el arte: en el modelo sí llega, y de eso
        depende que la noche pueda perderse por ella."""
        assert nombres.FLORINDA in habitaciones_posibles()["primer_patio"]

    def test_en_las_demas_camaras_no_cambia_nada(self):
        for id_habitacion, quienes in habitaciones_posibles().items():
            if id_habitacion == "primer_patio":
                continue
            assert habitaciones_que_se_dibujan()[id_habitacion] == quienes

    def test_los_demas_siguen_necesitando_su_imagen_en_el_patio(self):
        """Todos menos Doña Florinda (llegada mortal) y Doña Clotilde, que
        nunca llega al patio: mata desde su cámara."""
        dibujables = habitaciones_que_se_dibujan()["primer_patio"]
        assert set(dibujables) == {
            c.nombre for c in ELENCO
            if c.nombre not in (nombres.FLORINDA, nombres.CLOTILDE)
        }


class TestHabitacionesPosibles:
    def test_solo_lista_habitaciones_que_existen(self):
        assert set(habitaciones_posibles()).issubset(set(HABITACIONES))

    def test_todos_menos_la_bruja_pueden_llegar_al_patio_del_jugador(self):
        en_el_patio = set(habitaciones_posibles()["primer_patio"])
        assert en_el_patio == {c.nombre for c in ELENCO if c.nombre != nombres.CLOTILDE}

    def test_cada_personaje_aparece_en_su_casa_de_origen(self):
        posibles = habitaciones_posibles()
        for config in ELENCO:
            for inicio in (config.habitacion_inicial, *config.aparece_en):
                if inicio is not None:
                    assert config.nombre in posibles[inicio]

    def test_la_bruja_puede_aparecer_en_cualquier_camara_menos_el_patio(self):
        posibles = habitaciones_posibles()
        for id_habitacion in HABITACIONES:
            dentro = nombres.CLOTILDE in posibles.get(id_habitacion, [])
            assert dentro == (id_habitacion != "primer_patio"), id_habitacion

    def test_jaimico_solo_aparece_en_su_casa_y_en_el_patio(self):
        posibles = habitaciones_posibles()
        donde = {h for h, quienes in posibles.items() if nombres.JAIMICO in quienes}
        assert donde == {"casa_jaimito", "primer_patio"}
