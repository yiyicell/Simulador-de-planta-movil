"""
Gestión de sustratos.

Catálogo de tipos de sustrato pre-cargados en la base de datos:
  - corteza        : Corteza de pino. Excelente drenaje, poca retención. Ideal orquídeas.
  - musgo_sphagnum : Musgo sphagnum. Alta retención de humedad y agua.
  - perlita        : Perlita volcánica. Drenaje máximo, retención mínima.
  - mixto          : Mezcla balanceada. Factor 1.0 en todo.

water_retention: multiplicador sobre los ml regados → más alto = más agua queda en el sustrato.
drainage_factor: velocidad de drenaje relativa → más alto = el agua pasa más rápido.
"""

try:
    from backend.database import get_connection
    from backend.plant.models import TipoSustrato
    from backend.plant.history import registrar_accion
except ModuleNotFoundError:
    from database import get_connection
    from plant.models import TipoSustrato
    from plant.history import registrar_accion


def obtener_tipos_sustrato() -> dict:
    """
    Retorna el catálogo completo de tipos de sustrato.

    Retorna:
        dict con "exito" y "sustratos" (list[TipoSustrato]).
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id_substrate_type, name, description,
                   water_retention, nutrient_release, drainage_factor
            FROM substrate_type
            ORDER BY id_substrate_type
            """
        )
        rows = cursor.fetchall()
        sustratos = [
            TipoSustrato(
                id_substrate_type=r[0],
                name=r[1],
                description=r[2] or "",
                water_retention=r[3] or 1.0,
                nutrient_release=r[4] or 1.0,
                drainage_factor=r[5] or 1.0,
            )
            for r in rows
        ]
        return {"exito": True, "sustratos": sustratos}
    except Exception as e:
        return {"exito": False, "sustratos": [], "mensaje": str(e)}
    finally:
        conn.close()


def asignar_sustrato(plant_id: int, substrate_type_id: int) -> dict:
    """
    Cambia el sustrato de la planta y registra la acción en el historial.

    Retorna:
        dict con "exito", "mensaje" y "sustrato" (TipoSustrato).
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Verificar que la planta exista
        cursor.execute("SELECT id_plant FROM plant WHERE id_plant = %s", (plant_id,))
        if not cursor.fetchone():
            return {"exito": False, "mensaje": "Planta no encontrada.", "sustrato": None}

        # Verificar que el tipo de sustrato exista
        cursor.execute(
            """
            SELECT id_substrate_type, name, description,
                   water_retention, nutrient_release, drainage_factor
            FROM substrate_type
            WHERE id_substrate_type = %s
            """,
            (substrate_type_id,),
        )
        row = cursor.fetchone()
        if not row:
            return {"exito": False, "mensaje": "Tipo de sustrato no encontrado.", "sustrato": None}

        sustrato = TipoSustrato(
            id_substrate_type=row[0],
            name=row[1],
            description=row[2] or "",
            water_retention=row[3] or 1.0,
            nutrient_release=row[4] or 1.0,
            drainage_factor=row[5] or 1.0,
        )

        # Actualizar la planta
        cursor.execute(
            "UPDATE plant SET fk_substrate_type = %s WHERE id_plant = %s",
            (substrate_type_id, plant_id),
        )

        # Registrar en historial dentro de la misma transacción
        registrar_accion(
            plant_id=plant_id,
            action_type="sustrato",
            value=float(substrate_type_id),
            extra_info=f"Sustrato cambiado a: {sustrato.name}",
            conn=conn,
        )

        conn.commit()
        return {
            "exito": True,
            "mensaje": f"Sustrato cambiado a '{sustrato.name}' correctamente.",
            "sustrato": sustrato,
        }
    except Exception as e:
        conn.rollback()
        return {"exito": False, "mensaje": f"Error al cambiar el sustrato: {e}", "sustrato": None}
    finally:
        conn.close()


def obtener_sustrato_planta(plant_id: int) -> TipoSustrato | None:
    """
    Retorna el tipo de sustrato asignado a la planta o None si no tiene.
    Uso interno para calcular el factor de absorción al regar.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT st.id_substrate_type, st.name, st.description,
                   st.water_retention, st.nutrient_release, st.drainage_factor
            FROM plant p
            JOIN substrate_type st ON st.id_substrate_type = p.fk_substrate_type
            WHERE p.id_plant = %s
            """,
            (plant_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return TipoSustrato(
            id_substrate_type=row[0],
            name=row[1],
            description=row[2] or "",
            water_retention=row[3] or 1.0,
            nutrient_release=row[4] or 1.0,
            drainage_factor=row[5] or 1.0,
        )
    finally:
        conn.close()
