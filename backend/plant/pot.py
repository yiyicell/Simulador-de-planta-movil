"""
Gestión de la maceta asociada a una planta.

Propiedades físicas:
  - material        : plastico | ceramica | terracota | vidrio
  - size_cm         : diámetro en cm (tamaño único por ahora: 15 cm)
  - drainage_level  : nivel de drenaje de los orificios (0–100)
  - ventilation_level: ventilación estructural de la maceta (ranuras, rejillas, 0–100)

Nota: `pot.ventilation_level` describe los huecos físicos de la maceta (fijo hasta
replantar). `plant.ventilation_level` es la circulación ambiental que controla el usuario.
"""

try:
    from backend.database import get_connection
    from backend.plant.models import Maceta
    from backend.plant.history import registrar_accion
except ModuleNotFoundError:
    from database import get_connection
    from plant.models import Maceta
    from plant.history import registrar_accion

MATERIALES_VALIDOS = {"plastico", "ceramica", "terracota", "vidrio"}
TAMANIO_DEFAULT    = 15   # cm de diámetro


def crear_maceta_default(plant_id: int, conn) -> None:
    """
    Crea una maceta con valores por defecto al crear una planta.
    Debe llamarse dentro de una transacción activa (conn ya abierto).
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO pot (material, size_cm, drainage_level, ventilation_level, fk_plant_id)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (fk_plant_id) DO NOTHING
        """,
        ("plastico", TAMANIO_DEFAULT, 60.0, 50.0, plant_id),
    )


def obtener_maceta(plant_id: int) -> dict:
    """
    Retorna la maceta asociada a la planta.

    Retorna:
        dict con "exito", "mensaje" y "maceta" (Maceta | None).
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id_pot, material, size_cm, drainage_level, ventilation_level, fk_plant_id
            FROM pot
            WHERE fk_plant_id = %s
            """,
            (plant_id,),
        )
        row = cursor.fetchone()
        if not row:
            return {"exito": False, "mensaje": "Maceta no encontrada para esta planta.", "maceta": None}
        maceta = Maceta(
            id_pot=row[0],
            material=row[1],
            size_cm=row[2],
            drainage_level=row[3] or 60.0,
            ventilation_level=row[4] or 50.0,
            fk_plant_id=row[5],
        )
        return {"exito": True, "maceta": maceta}
    except Exception as e:
        return {"exito": False, "mensaje": str(e), "maceta": None}
    finally:
        conn.close()


def actualizar_maceta(
    plant_id: int,
    material: str | None = None,
    drainage_level: float | None = None,
    ventilation_level: float | None = None,
) -> dict:
    """
    Actualiza los atributos físicos de la maceta.
    Solo los campos provistos (no None) son modificados.

    Retorna:
        dict con "exito", "mensaje" y "maceta" (Maceta actualizada).
    """
    if material is not None and material.lower() not in MATERIALES_VALIDOS:
        return {
            "exito": False,
            "mensaje": f"Material no válido. Opciones: {', '.join(MATERIALES_VALIDOS)}.",
            "maceta": None,
        }
    if drainage_level is not None and not (0.0 <= drainage_level <= 100.0):
        return {"exito": False, "mensaje": "drainage_level debe estar entre 0 y 100.", "maceta": None}
    if ventilation_level is not None and not (0.0 <= ventilation_level <= 100.0):
        return {"exito": False, "mensaje": "ventilation_level debe estar entre 0 y 100.", "maceta": None}

    campos = {}
    if material is not None:
        campos["material"] = material.lower()
    if drainage_level is not None:
        campos["drainage_level"] = round(drainage_level, 2)
    if ventilation_level is not None:
        campos["ventilation_level"] = round(ventilation_level, 2)

    if not campos:
        return {"exito": False, "mensaje": "No se proporcionaron campos a actualizar.", "maceta": None}

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id_pot FROM pot WHERE fk_plant_id = %s", (plant_id,))
        if not cursor.fetchone():
            return {"exito": False, "mensaje": "Maceta no encontrada para esta planta.", "maceta": None}

        set_clause = ", ".join(f"{k} = %s" for k in campos)
        valores = list(campos.values()) + [plant_id]
        cursor.execute(f"UPDATE pot SET {set_clause} WHERE fk_plant_id = %s", valores)

        extra = ", ".join(f"{k}={v}" for k, v in campos.items())
        registrar_accion(
            plant_id=plant_id,
            action_type="maceta",
            value=0.0,
            extra_info=f"Maceta actualizada: {extra}",
            conn=conn,
        )

        conn.commit()

        # Retornar maceta actualizada
        cursor.execute(
            """
            SELECT id_pot, material, size_cm, drainage_level, ventilation_level, fk_plant_id
            FROM pot WHERE fk_plant_id = %s
            """,
            (plant_id,),
        )
        row = cursor.fetchone()
        maceta = Maceta(
            id_pot=row[0],
            material=row[1],
            size_cm=row[2],
            drainage_level=row[3],
            ventilation_level=row[4],
            fk_plant_id=row[5],
        )
        return {"exito": True, "mensaje": "Maceta actualizada correctamente.", "maceta": maceta}
    except Exception as e:
        conn.rollback()
        return {"exito": False, "mensaje": f"Error al actualizar la maceta: {e}", "maceta": None}
    finally:
        conn.close()
