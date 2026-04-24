"""
Lógica de economía (Plantastic Coins) y tienda base.

Incluye:
    - Consulta de saldo desde user.coins
    - Recompensa de coins por cuidado óptimo
    - Listado de ítems de tienda
    - Compra de ítems con validación de saldo
    - Inventario del usuario
"""

try:
    from backend.database import get_connection
except ModuleNotFoundError:
    from database import get_connection


RECOMPENSA_CUIDADO_OPTIMO = 1


def _registrar_movimiento(
    user_id: int,
    amount: int,
    movement_type: str,
    reason: str,
    related_plant_id: int | None,
    related_item_id: int | None,
    conn,
) -> None:
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO coin_transaction (
            fk_user_id, amount, movement_type, reason, related_plant_id, related_item_id
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (user_id, amount, movement_type, reason, related_plant_id, related_item_id),
    )


def obtener_saldo(user_id: int) -> dict:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT coins FROM "user" WHERE user_id = %s', (user_id,))
        row = cursor.fetchone()
        if row is None:
            return {"exito": False, "mensaje": "Usuario no encontrado."}
        return {
            "exito": True,
            "user_id": user_id,
            "coins_balance": int(row[0]),
        }
    except Exception as e:
        return {"exito": False, "mensaje": f"Error al consultar saldo: {e}"}
    finally:
        conn.close()


def sumar_coins_por_cuidado(user_id: int, plant_id: int, coins: int = RECOMPENSA_CUIDADO_OPTIMO, conn=None) -> None:
    """
    Suma coins por cuidado óptimo usando conexión existente (misma transacción)
    o una conexión nueva si no se pasa `conn`.
    """
    if coins <= 0:
        return

    propietario_conn = conn is None
    if propietario_conn:
        conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE "user"
            SET coins = coins + %s
            WHERE user_id = %s
            """,
            (coins, user_id),
        )
        if cursor.rowcount == 0:
            raise ValueError("Usuario no encontrado para sumar coins.")
        _registrar_movimiento(
            user_id=user_id,
            amount=coins,
            movement_type="credito",
            reason="cuidado_optimo",
            related_plant_id=plant_id,
            related_item_id=None,
            conn=conn,
        )
        if propietario_conn:
            conn.commit()
    except Exception:
        if propietario_conn:
            conn.rollback()
        raise
    finally:
        if propietario_conn:
            conn.close()


def listar_items(item_type: str | None = None) -> dict:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if item_type:
            cursor.execute(
                """
                SELECT id_item, item_name, item_type, price_coins, rarity, active
                FROM shop_item
                WHERE active = TRUE AND item_type = %s
                ORDER BY price_coins ASC, id_item ASC
                """,
                (item_type,),
            )
        else:
            cursor.execute(
                """
                SELECT id_item, item_name, item_type, price_coins, rarity, active
                FROM shop_item
                WHERE active = TRUE
                ORDER BY item_type ASC, price_coins ASC, id_item ASC
                """
            )

        rows = cursor.fetchall()
        return {
            "exito": True,
            "items": [
                {
                    "id_item": r[0],
                    "item_name": r[1],
                    "item_type": r[2],
                    "price_coins": int(r[3]),
                    "rarity": r[4],
                    "active": bool(r[5]),
                }
                for r in rows
            ],
        }
    except Exception as e:
        return {"exito": False, "mensaje": f"Error al listar ítems: {e}", "items": []}
    finally:
        conn.close()


def comprar_item(user_id: int, item_id: int, quantity: int = 1) -> dict:
    if quantity <= 0:
        return {"exito": False, "mensaje": "La cantidad debe ser mayor que 0."}

    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id_item, item_name, item_type, price_coins
            FROM shop_item
            WHERE id_item = %s AND active = TRUE
            """,
            (item_id,),
        )
        item = cursor.fetchone()
        if not item:
            return {"exito": False, "mensaje": "Ítem no encontrado o inactivo."}

        price = int(item[3])
        total_cost = price * quantity

        cursor.execute(
            'SELECT coins FROM "user" WHERE user_id = %s FOR UPDATE',
            (user_id,),
        )
        user_row = cursor.fetchone()
        if user_row is None:
            conn.rollback()
            return {"exito": False, "mensaje": "Usuario no encontrado."}
        saldo_actual = int(user_row[0])

        if saldo_actual < total_cost:
            conn.rollback()
            return {
                "exito": False,
                "mensaje": "Saldo insuficiente para completar la compra.",
                "coins_balance": saldo_actual,
                "costo": total_cost,
            }

        cursor.execute(
            """
            UPDATE "user"
            SET coins = coins - %s
            WHERE user_id = %s
            """,
            (total_cost, user_id),
        )

        cursor.execute(
            """
            INSERT INTO user_inventory (fk_user_id, fk_item_id, quantity)
            VALUES (%s, %s, %s)
            ON CONFLICT (fk_user_id, fk_item_id)
            DO UPDATE SET quantity = user_inventory.quantity + EXCLUDED.quantity
            """,
            (user_id, item_id, quantity),
        )

        _registrar_movimiento(
            user_id=user_id,
            amount=-total_cost,
            movement_type="debito",
            reason=f"compra:{item[1]}",
            related_plant_id=None,
            related_item_id=item_id,
            conn=conn,
        )

        cursor.execute(
            'SELECT coins FROM "user" WHERE user_id = %s',
            (user_id,),
        )
        saldo_nuevo = int(cursor.fetchone()[0])

        conn.commit()
        return {
            "exito": True,
            "mensaje": "Compra realizada con éxito.",
            "item": {
                "id_item": item[0],
                "item_name": item[1],
                "item_type": item[2],
                "price_coins": price,
            },
            "quantity": quantity,
            "costo": total_cost,
            "coins_balance": saldo_nuevo,
        }
    except Exception as e:
        conn.rollback()
        return {"exito": False, "mensaje": f"Error al comprar ítem: {e}"}
    finally:
        conn.close()


def obtener_inventario(user_id: int) -> dict:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT i.id_inventory, s.id_item, s.item_name, s.item_type,
                   s.rarity, i.quantity, i.acquired_at
            FROM user_inventory i
            INNER JOIN shop_item s ON s.id_item = i.fk_item_id
            WHERE i.fk_user_id = %s
            ORDER BY s.item_type ASC, s.item_name ASC
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
        return {
            "exito": True,
            "inventario": [
                {
                    "id_inventory": r[0],
                    "id_item": r[1],
                    "item_name": r[2],
                    "item_type": r[3],
                    "rarity": r[4],
                    "quantity": int(r[5]),
                    "acquired_at": str(r[6]),
                }
                for r in rows
            ],
        }
    except Exception as e:
        return {"exito": False, "mensaje": f"Error al consultar inventario: {e}", "inventario": []}
    finally:
        conn.close()