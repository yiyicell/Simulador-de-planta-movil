"""
Historial de acciones de cuidado de la planta.

Cada vez que el usuario realiza una acción (regar, ajustar luz, cambiar sustrato, etc.),
se registra en la tabla `care_history` con:
  - tipo de acción
  - valor principal (ml, intensidad, etc.)
  - información adicional (texto libre, p.ej. nombre del sustrato)
  - timestamp automático

Este módulo expone:
  - registrar_accion()  — llamado internamente desde care.py / substrate.py / pot.py
  - obtener_historial() — llamado desde el endpoint GET /plants/{id}/history
"""

try:
    from backend.database import get_connection
    from backend.plant.models import HistorialAccion
except ModuleNotFoundError:
    from database import get_connection
    from plant.models import HistorialAccion

# Tipos de acción válidos
TIPOS_ACCION = {"riego", "luz", "ventilacion", "sustrato", "maceta"}


def registrar_accion(
    plant_id: int,
    action_type: str,
    value: float,
    extra_info: str = "",
    conn=None,
) -> None:
    """
    Inserta un registro en care_history.

    Puede recibir una conexión activa (conn) para ejecutar dentro de la misma
    transacción que la acción principal. Si no se pasa conn, abre y cierra una propia.
    """
    propietario_conn = conn is None
    if propietario_conn:
        conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO care_history (fk_plant_id, action_type, value, extra_info)
            VALUES (%s, %s, %s, %s)
            """,
            (plant_id, action_type, value, extra_info),
        )
        if propietario_conn:
            conn.commit()
    finally:
        if propietario_conn:
            conn.close()


def obtener_historial(plant_id: int, limit: int = 50) -> dict:
    """
    Retorna el historial de acciones de la planta, ordenado del más reciente al más antiguo.

    Args:
        plant_id: ID de la planta.
        limit:    Máximo de registros a devolver (por defecto 50, máximo 200).

    Retorna:
        dict con:
          - "exito" (bool)
          - "historial" (list[HistorialAccion])
          - "total" (int)
    """
    limit = min(max(1, limit), 200)
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Total de registros
        cursor.execute(
            "SELECT COUNT(*) FROM care_history WHERE fk_plant_id = %s",
            (plant_id,),
        )
        total = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT id_history, fk_plant_id, action_type, value, extra_info,
                   TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') AS created_at
            FROM care_history
            WHERE fk_plant_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (plant_id, limit),
        )
        rows = cursor.fetchall()
        historial = [
            HistorialAccion(
                id_history=r[0],
                fk_plant_id=r[1],
                action_type=r[2],
                value=r[3] or 0.0,
                extra_info=r[4] or "",
                created_at=r[5],
            )
            for r in rows
        ]
        return {"exito": True, "historial": historial, "total": total}
    except Exception as e:
        return {"exito": False, "historial": [], "total": 0, "mensaje": str(e)}
    finally:
        conn.close()
