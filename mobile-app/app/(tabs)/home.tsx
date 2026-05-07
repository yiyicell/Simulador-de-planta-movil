import { router } from 'expo-router'
import React, { useEffect, useMemo, useRef, useState } from 'react'
import {
  ActivityIndicator,
  Animated,
  Image,
  LayoutChangeEvent,
  Modal,
  PanResponder,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native'

import { API_BASE_URL } from '@/constants/api'
import { useSession } from '@/context/session'

type ClaveModal =
  | 'perfil'
  | 'opciones'
  | 'salud'
  | 'maceta'
  | 'tienda'
  | 'sustrato'
  | 'historial'
  | 'intensidad'
  | 'riego'

type EstadoPlanta = {
  id_plant: number
  plant_name: string
  plant_type: string
  water_level: number
  light_level: number
  humidity_level: number
  ventilation_level: number
  health: number
  growth_stage: string
  total_care_actions: number
  creation_date_plant: string
  substrate_name: string
}

type EstadoRespuesta = {
  planta: EstadoPlanta
  salud_etiqueta: string
  etapa_descripcion: string
  alertas: string[]
}

type MacetaRespuesta = {
  maceta: {
    id_pot: number
    material: string
    size_cm: number
    drainage_level: number
    ventilation_level: number
    fk_plant_id: number
  }
}

type SustratoCatalogo = {
  id_substrate_type: number
  name: string
  description: string
  water_retention: number
  nutrient_release: number
  drainage_factor: number
}

type HistorialItem = {
  id_history: number
  action_type: string
  value: number
  extra_info: string
  created_at: string
}

type ItemTienda = {
  id_item: number
  item_name: string
  item_type: string
  price_coins: number
  rarity: string
  active: boolean
}

type ItemInventario = {
  id_inventory: number
  id_item: number
  item_name: string
  item_type: string
  rarity: string
  quantity: number
  acquired_at: string
}

type PresetMaceta = {
  material: 'plastico' | 'ceramica' | 'terracota' | 'vidrio'
  drainage_level: number
  ventilation_level: number
}

type LayoutEtapa = {
  width: number
  height: number
  marginBottom: number
  translateX: number
  centrarImagen?: boolean
}

const imagenes = {
  perfil: require('../../assets/images/profile.png'),
  opciones: require('../../assets/images/options.png'),
  info: require('../../assets/images/information.png'),
  flecha: require('../../assets/images/arrow.png'),

  indicadorLuz: require('../../assets/images/ind-light-bulb.png'),
  indicadorHumedad: require('../../assets/images/ind-humidity.png'),
  indicadorAgua: require('../../assets/images/ind-water-drop.png'),
  indicadorSustrato: require('../../assets/images/ind-soil.png'),

  maceta: require('../../assets/images/hot-plant-pot.png'),
  sustrato: require('../../assets/images/hot-soil-bag.png'),
  historial: require('../../assets/images/hot-history.png'),
  intensidad: require('../../assets/images/hot-ceiling-lamp.png'),
  riego: require('../../assets/images/hot-watering-can.png'),
  orquidea: require('../../assets/images/orchid-select.png'),
}

const imagenesEtapas: Record<string, any> = {
  germinacion: require('../../assets/images/seed-pot1.png'),
  enraizamiento: require('../../assets/images/enraizamiento-pot1.png'),
  plantula: require('../../assets/images/plantula-pot1.png'),
  crecimiento: require('../../assets/images/crecimiento-pot1.png'),
  vara_floral: require('../../assets/images/vara_floral-pot1.png'),
  botones_florales: require('../../assets/images/botones_florales-pot1.png'),
  crecimiento_botones: require('../../assets/images/crecimiento_botones-pot1.png'),
  apertura_petalos: require('../../assets/images/apertura_petalos-pot1.png'),
}

const MAX_RIEGO_ML = 1000
const PASO_RIEGO_ML = 50
const PASO_LUZ = 5
const TUNNEL_HEADERS = {
  'bypass-tunnel-reminder': 'true',
}

function clamp(valor: number) {
  return Math.max(0, Math.min(100, valor))
}

function formatearEtapa(etapa?: string) {
  if (!etapa) {
    return 'Sin etapa'
  }

  return etapa
    .split('_')
    .map((parte) => parte.charAt(0).toUpperCase() + parte.slice(1))
    .join(' ')
}

function obtenerImagenEtapa(etapa?: string) {
  return etapa
    ? imagenesEtapas[etapa] || imagenesEtapas.germinacion
    : imagenesEtapas.germinacion
}

function obtenerLayoutEtapa(etapa?: string): LayoutEtapa {
  switch (etapa) {
    case 'germinacion':
    case 'enraizamiento':
      return {
        width: 238,
        height: 286,
        marginBottom: -6,
        translateX: 0,
        centrarImagen: true,
      }
    case 'plantula':
      return {
        width: 238,
        height: 286,
        marginBottom: -6,
        translateX: 0,
        centrarImagen: true,
      }
    case 'crecimiento':
      return {
        width: 238,
        height: 286,
        marginBottom: -6,
        translateX: -24,
      }
    case 'vara_floral':
      return {
        width: 270,
        height: 430,
        marginBottom: -82,
        translateX: 10,
      }
    case 'botones_florales':
    case 'crecimiento_botones':
    case 'apertura_petalos':
      return {
        width: 270,
        height: 410,
        marginBottom: -72,
        translateX: -25,
      }
    default:
      return {
        width: 238,
        height: 286,
        marginBottom: -6,
        translateX: 0,
        centrarImagen: true,
      }
  }
}

function obtenerPresetMaceta(itemName: string): PresetMaceta {
  const nombre = itemName.toLowerCase()

  if (nombre.includes('barro')) {
    return {
      material: 'terracota',
      drainage_level: 72,
      ventilation_level: 78,
    }
  }

  if (nombre.includes('blanca') || nombre.includes('minimalista')) {
    return {
      material: 'ceramica',
      drainage_level: 64,
      ventilation_level: 58,
    }
  }

  if (nombre.includes('vidrio')) {
    return {
      material: 'vidrio',
      drainage_level: 48,
      ventilation_level: 42,
    }
  }

  return {
    material: 'plastico',
    drainage_level: 60,
    ventilation_level: 50,
  }
}

function colorBarra(valor: number) {
  if (valor >= 70) {
    return '#46a11f'
  }

  if (valor >= 35) {
    return '#dca63a'
  }

  return '#b63838'
}

function formatearAccion(tipo: string) {
  switch (tipo) {
    case 'water':
      return 'Riego'
    case 'light':
      return 'Luz'
    case 'ventilacion':
      return 'Ventilacion'
    case 'substrato':
      return 'Sustrato'
    case 'maceta':
      return 'Maceta'
    default:
      return tipo
    }
}

function descripcionSustratoNeutral(sustrato?: SustratoCatalogo) {
  if (!sustrato) {
    return 'Sin descripcion disponible.'
  }

  const rasgos: string[] = []

  if (sustrato.water_retention >= 1.3) {
    rasgos.push('retiene humedad con facilidad')
  } else if (sustrato.water_retention <= 0.8) {
    rasgos.push('pierde humedad rapidamente')
  } else {
    rasgos.push('mantiene una humedad equilibrada')
  }

  if (sustrato.drainage_factor >= 1.3) {
    rasgos.push('drena con rapidez')
  } else if (sustrato.drainage_factor <= 0.8) {
    rasgos.push('drena lentamente')
  } else {
    rasgos.push('tiene un drenaje moderado')
  }

  if (sustrato.nutrient_release >= 1.2) {
    rasgos.push('libera nutrientes con mas intensidad')
  } else if (sustrato.nutrient_release <= 0.8) {
    rasgos.push('libera nutrientes de forma ligera')
  } else {
    rasgos.push('libera nutrientes de forma estable')
  }

  return `${sustrato.name} tiene un comportamiento particular: ${rasgos.join(', ')}.`
}

export default function HomeScreen() {
  const [modalActivo, setModalActivo] = useState<ClaveModal | null>(null)
  const [cerrandoSesion, setCerrandoSesion] = useState(false)
  const [cargandoPantalla, setCargandoPantalla] = useState(true)
  const [cargandoModal, setCargandoModal] = useState(false)
  const [ejecutandoAccion, setEjecutandoAccion] = useState(false)
  const [errorModal, setErrorModal] = useState('')
  const [errorInventario, setErrorInventario] = useState('')
  const [estado, setEstado] = useState<EstadoRespuesta | null>(null)
  const [maceta, setMaceta] = useState<MacetaRespuesta['maceta'] | null>(null)
  const [sustratos, setSustratos] = useState<SustratoCatalogo[]>([])
  const [historial, setHistorial] = useState<HistorialItem[]>([])
  const [itemsTienda, setItemsTienda] = useState<ItemTienda[]>([])
  const [inventario, setInventario] = useState<ItemInventario[]>([])
  const [coinsBalance, setCoinsBalance] = useState<number | null>(null)
  const [itemComprandoId, setItemComprandoId] = useState<number | null>(null)
  const [cantidadRiego, setCantidadRiego] = useState('')
  const [intensidadLuz, setIntensidadLuz] = useState('')
  const [feedbackVisual, setFeedbackVisual] = useState('')
  const [sustratoSeleccionadoId, setSustratoSeleccionadoId] = useState<number | null>(
    null
  )
  const [altoControlLuz, setAltoControlLuz] = useState(0)
  const [anchoControlRiego, setAnchoControlRiego] = useState(0)
  const { plantaActual, usuario, cerrarSesionLocal } = useSession()
  const animacionPlanta = useRef(new Animated.Value(1)).current
  const inicioLuzRef = useRef(0)
  const inicioRiegoRef = useRef(0)
  const intensidadActualRef = useRef(0)
  const riegoActualRef = useRef(0)
  const altoControlLuzRef = useRef(0)
  const anchoControlRiegoRef = useRef(0)

  useEffect(() => {
    if (!usuario) {
      router.replace('/login')
      return
    }

    if (!plantaActual) {
      router.replace('/select-plant')
    }
  }, [plantaActual, usuario])

  useEffect(() => {
    if (!plantaActual?.id) {
      return
    }

    cargarEstado(true)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [plantaActual?.id])

  useEffect(() => {
    if (!usuario?.id) {
      return
    }

    void cargarSaldo()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [usuario?.id])

  const abrirModal = (clave: ClaveModal) => {
    setErrorModal('')
    setErrorInventario('')
    setModalActivo(clave)
  }

  const cerrarModal = () => {
    if (ejecutandoAccion) {
      return
    }

    setModalActivo(null)
    setErrorModal('')
    setErrorInventario('')
  }

  const animarCambio = (mensaje: string) => {
    setFeedbackVisual(mensaje)

    Animated.sequence([
      Animated.timing(animacionPlanta, {
        toValue: 1.08,
        duration: 160,
        useNativeDriver: true,
      }),
      Animated.spring(animacionPlanta, {
        toValue: 1,
        friction: 5,
        tension: 120,
        useNativeDriver: true,
      }),
    ]).start()

    setTimeout(() => {
      setFeedbackVisual((actual) => (actual === mensaje ? '' : actual))
    }, 1800)
  }

  const cargarEstado = async (mostrarCarga = false) => {
    if (!plantaActual?.id) {
      return
    }

    if (mostrarCarga) {
      setCargandoPantalla(true)
    }

    try {
      const respuesta = await fetch(
        `${API_BASE_URL}/plants/${plantaActual.id}/status`
      )
      const texto = await respuesta.text()
      let datos: any = {}

      try {
        datos = JSON.parse(texto)
      } catch {
        datos = {}
      }

      if (!respuesta.ok) {
        setErrorModal(datos.mensaje || 'No se pudo consultar el estado')
        return
      }

      setEstado(datos)
      setCantidadRiego((actual) => actual || '250')
      setIntensidadLuz((actual) =>
        actual || String(Math.round(datos.planta?.light_level ?? 50))
      )
    } catch (error) {
      console.log('Error consultando estado:', error)
      setErrorModal('No se pudo conectar con el servidor')
    } finally {
      setCargandoPantalla(false)
    }
  }

  useEffect(() => {
    if (!modalActivo || !plantaActual?.id) {
      return
    }

    if (modalActivo === 'maceta') {
      void cargarMaceta()
      void cargarInventario()
      void cargarSaldo()
    }

    if (modalActivo === 'tienda') {
      void cargarTiendaMacetas()
      void cargarInventario()
      void cargarSaldo()
    }

    if (modalActivo === 'sustrato') {
      setSustratoSeleccionadoId(null)
      void cargarSustratos()
    }

    if (modalActivo === 'historial') {
      void cargarHistorial()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modalActivo, plantaActual?.id])

  const cargarMaceta = async () => {
    if (!plantaActual?.id) {
      return
    }

    setCargandoModal(true)

    try {
      const respuesta = await fetch(`${API_BASE_URL}/plants/${plantaActual.id}/pot`)
      const texto = await respuesta.text()
      let datos: any = {}

      try {
        datos = JSON.parse(texto)
      } catch {
        datos = {}
      }

      if (!respuesta.ok) {
        setErrorModal(datos.mensaje || 'No se pudo consultar la maceta')
        return
      }

      setMaceta(datos.maceta)
    } catch (error) {
      console.log('Error consultando maceta:', error)
      setErrorModal('No se pudo conectar con el servidor')
    } finally {
      setCargandoModal(false)
    }
  }

  const cargarSustratos = async () => {
    setCargandoModal(true)

    try {
      const respuesta = await fetch(`${API_BASE_URL}/plants/substrates`)
      const texto = await respuesta.text()
      let datos: any = {}

      try {
        datos = JSON.parse(texto)
      } catch {
        datos = {}
      }

      if (!respuesta.ok) {
        setErrorModal(datos.mensaje || 'No se pudo consultar el sustrato')
        return
      }

      const catalogo = datos.sustratos || []
      setSustratos(catalogo)

      const sustratoActivo = catalogo.find(
        (sustrato: SustratoCatalogo) =>
          sustrato.name.toLowerCase() ===
          (estado?.planta.substrate_name || '').toLowerCase()
      )

      setSustratoSeleccionadoId(
        sustratoActivo?.id_substrate_type || catalogo[0]?.id_substrate_type || null
      )
    } catch (error) {
      console.log('Error consultando sustratos:', error)
      setErrorModal('No se pudo conectar con el servidor')
    } finally {
      setCargandoModal(false)
    }
  }

  const cargarHistorial = async () => {
    if (!plantaActual?.id) {
      return
    }

    setCargandoModal(true)

    try {
      const respuesta = await fetch(
        `${API_BASE_URL}/plants/${plantaActual.id}/history?limit=8`
      )
      const texto = await respuesta.text()
      let datos: any = {}

      try {
        datos = JSON.parse(texto)
      } catch {
        datos = {}
      }

      if (!respuesta.ok) {
        setErrorModal(datos.mensaje || 'No se pudo consultar el historial')
        return
      }

      setHistorial(datos.historial || [])
    } catch (error) {
      console.log('Error consultando historial:', error)
      setErrorModal('No se pudo conectar con el servidor')
    } finally {
      setCargandoModal(false)
    }
  }

  const cargarSaldo = async () => {
    if (!usuario?.id) {
      return
    }

    try {
      const respuesta = await fetch(
        `${API_BASE_URL}/economy/users/${usuario.id}/wallet`,
        {
          headers: TUNNEL_HEADERS,
        }
      )
      const texto = await respuesta.text()
      let datos: any = {}

      try {
        datos = JSON.parse(texto)
      } catch {
        datos = {}
      }

      if (!respuesta.ok) {
        setErrorModal(datos.mensaje || 'No se pudo consultar tus monedas')
        return
      }

      setCoinsBalance(Number(datos.coins_balance) || 0)
    } catch (error) {
      console.log('Error consultando monedas:', error)
      setErrorModal('No se pudo conectar con el servidor')
    }
  }

  const cargarTiendaMacetas = async () => {
    setCargandoModal(true)

    try {
      const respuesta = await fetch(`${API_BASE_URL}/shop/items?item_type=maceta`, {
        headers: TUNNEL_HEADERS,
      })
      const texto = await respuesta.text()
      let datos: any = {}

      try {
        datos = JSON.parse(texto)
      } catch {
        datos = {}
      }

      if (!respuesta.ok) {
        setErrorModal(datos.mensaje || 'No se pudo consultar la tienda')
        return
      }

      setItemsTienda(datos.items || [])
    } catch (error) {
      console.log('Error consultando tienda:', error)
      setErrorModal('No se pudo conectar con el servidor')
    } finally {
      setCargandoModal(false)
    }
  }

  const cargarInventario = async () => {
    if (!usuario?.id) {
      return
    }

    try {
      setErrorInventario('')

      const respuesta = await fetch(`${API_BASE_URL}/shop/users/${usuario.id}/inventory`, {
        headers: TUNNEL_HEADERS,
      })
      const texto = await respuesta.text()
      let datos: any = {}

      try {
        datos = JSON.parse(texto)
      } catch {
        datos = {}
      }

      if (!respuesta.ok) {
        setErrorInventario(datos.mensaje || 'No se pudo consultar el inventario')
        return
      }

      setInventario(datos.inventario || [])
    } catch (error) {
      console.log('Error consultando inventario:', error)
      setErrorInventario('No se pudo conectar con el servidor')
    }
  }

  const comprarMaceta = async (item: ItemTienda) => {
    if (!usuario?.id || itemComprandoId) {
      return
    }

    setItemComprandoId(item.id_item)
    setErrorModal('')

    try {
      const respuesta = await fetch(`${API_BASE_URL}/shop/purchase`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...TUNNEL_HEADERS,
        },
        body: JSON.stringify({
          user_id: usuario.id,
          item_id: item.id_item,
          quantity: 1,
        }),
      })
      const texto = await respuesta.text()
      let datos: any = {}

      try {
        datos = JSON.parse(texto)
      } catch {
        datos = {}
      }

      if (!respuesta.ok) {
        setErrorModal(datos.mensaje || 'No se pudo comprar la maceta')
        if (typeof datos.coins_balance === 'number') {
          setCoinsBalance(datos.coins_balance)
        }
        return
      }

      setCoinsBalance(Number(datos.coins_balance) || 0)
      await cargarInventario()
      animarCambio(`${item.item_name} agregada al inventario`)
    } catch (error) {
      console.log('Error comprando maceta:', error)
      setErrorModal('No se pudo conectar con el servidor')
    } finally {
      setItemComprandoId(null)
    }
  }

  const equiparMaceta = async (nombreMaceta: string, preset: PresetMaceta) => {
    if (!plantaActual?.id || ejecutandoAccion) {
      return
    }

    setEjecutandoAccion(true)
    setErrorModal('')

    try {
      const respuesta = await fetch(`${API_BASE_URL}/plants/${plantaActual.id}/pot`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...TUNNEL_HEADERS,
        },
        body: JSON.stringify(preset),
      })
      const texto = await respuesta.text()
      let datos: any = {}

      try {
        datos = JSON.parse(texto)
      } catch {
        datos = {}
      }

      if (!respuesta.ok) {
        setErrorModal(datos.mensaje || 'No se pudo cambiar la maceta')
        return
      }

      setMaceta(datos.maceta)
      await cargarHistorial()
      animarCambio(`${nombreMaceta} equipada`)
    } catch (error) {
      console.log('Error cambiando maceta:', error)
      setErrorModal('No se pudo conectar con el servidor')
    } finally {
      setEjecutandoAccion(false)
    }
  }

  const manejarRiego = async () => {
    if (!plantaActual?.id || ejecutandoAccion) {
      return
    }

    const ml = Number(cantidadRiego)

    if (!Number.isFinite(ml) || ml <= 0) {
      setErrorModal('Ingresa una cantidad valida en ml')
      return
    }

    setEjecutandoAccion(true)
    setErrorModal('')

    try {
      const respuesta = await fetch(
        `${API_BASE_URL}/plants/${plantaActual.id}/water`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ cantidad_ml: ml }),
        }
      )

      const texto = await respuesta.text()
      let datos: any = {}

      try {
        datos = JSON.parse(texto)
      } catch {
        datos = {}
      }

      if (!respuesta.ok) {
        setErrorModal(datos.mensaje || 'No se pudo regar la planta')
        return
      }

      await cargarEstado()
      await cargarHistorial()
      await cargarSaldo()
      animarCambio(`Riego aplicado: ${Math.round(ml)} ml`)
      setModalActivo(null)
    } catch (error) {
      console.log('Error regando planta:', error)
      setErrorModal('No se pudo conectar con el servidor')
    } finally {
      setEjecutandoAccion(false)
    }
  }

  const manejarIntensidad = async () => {
    if (!plantaActual?.id || ejecutandoAccion) {
      return
    }

    const intensidad = Number(intensidadLuz)

    if (!Number.isFinite(intensidad) || intensidad < 0 || intensidad > 100) {
      setErrorModal('La intensidad debe estar entre 0 y 100')
      return
    }

    setEjecutandoAccion(true)
    setErrorModal('')

    try {
      const respuesta = await fetch(
        `${API_BASE_URL}/plants/${plantaActual.id}/light`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ intensidad }),
        }
      )

      const texto = await respuesta.text()
      let datos: any = {}

      try {
        datos = JSON.parse(texto)
      } catch {
        datos = {}
      }

      if (!respuesta.ok) {
        setErrorModal(datos.mensaje || 'No se pudo ajustar la luz')
        return
      }

      await cargarEstado()
      await cargarHistorial()
      await cargarSaldo()
      animarCambio(`Luz ajustada a ${Math.round(intensidad)}%`)
      setModalActivo(null)
    } catch (error) {
      console.log('Error ajustando luz:', error)
      setErrorModal('No se pudo conectar con el servidor')
    } finally {
      setEjecutandoAccion(false)
    }
  }

  const aplicarSustrato = async (sustratoId: number) => {
    if (!plantaActual?.id || ejecutandoAccion) {
      return
    }

    setEjecutandoAccion(true)
    setErrorModal('')

    try {
      const respuesta = await fetch(
        `${API_BASE_URL}/plants/${plantaActual.id}/substrate`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ substrate_type_id: sustratoId }),
        }
      )

      const texto = await respuesta.text()
      let datos: any = {}

      try {
        datos = JSON.parse(texto)
      } catch {
        datos = {}
      }

      if (!respuesta.ok) {
        setErrorModal(datos.mensaje || 'No se pudo cambiar el sustrato')
        return
      }

      await cargarEstado()
      animarCambio(`Sustrato: ${datos.sustrato?.name || 'actualizado'}`)
      setModalActivo(null)
    } catch (error) {
      console.log('Error cambiando sustrato:', error)
      setErrorModal('No se pudo conectar con el servidor')
    } finally {
      setEjecutandoAccion(false)
    }
  }

  const manejarCerrarSesion = async () => {
    if (!usuario || cerrandoSesion) {
      return
    }

    setCerrandoSesion(true)
    setErrorModal('')

    try {
      const respuesta = await fetch(`${API_BASE_URL}/auth/logout/${usuario.id}`, {
        method: 'POST',
      })

      const textoRespuesta = await respuesta.text()
      let datos: { mensaje?: string } = {}

      try {
        datos = JSON.parse(textoRespuesta)
      } catch {
        datos = {}
      }

      if (!respuesta.ok) {
        console.log('Logout no confirmado por backend:', datos.mensaje)
      }
    } catch (error) {
      console.log('Error logout:', error)
    } finally {
      cerrarSesionLocal()
      cerrarModal()
      router.replace('/login')
      setCerrandoSesion(false)
    }
  }

  const creadoTexto = usuario?.creado || 'Sin fecha registrada'
  const planta = estado?.planta
  const imagenEtapaActual = obtenerImagenEtapa(planta?.growth_stage)
  const layoutEtapa = obtenerLayoutEtapa(planta?.growth_stage)
  const intensidadActual = clamp(Number(intensidadLuz) || 0)
  const intensidadAplicada = clamp(planta?.light_level ?? 0)
  const opacidadLuzAmbiente = 0.02 + (intensidadAplicada / 100) * 0.08
  const opacidadConoLuz = 0.06 + (intensidadAplicada / 100) * 0.28
  const riegoActual = Math.max(
    0,
    Math.min(MAX_RIEGO_ML, Number(cantidadRiego) || 0)
  )
  const progresoRiego = riegoActual / MAX_RIEGO_ML
  const posicionMangoLuz = altoControlLuz
    ? (1 - intensidadActual / 100) * altoControlLuz - 18
    : 0
  const posicionMangoRiego = anchoControlRiego
    ? progresoRiego * Math.max(0, anchoControlRiego - 24)
    : 0
  const anchoRellenoRiego = anchoControlRiego
    ? progresoRiego * anchoControlRiego
    : 0

  const actualizarLuz = (valor: number) => {
    setIntensidadLuz(String(clamp(Math.round(valor))))
  }

  const actualizarRiego = (valor: number) => {
    const siguiente = Math.max(0, Math.min(MAX_RIEGO_ML, Math.round(valor)))
    setCantidadRiego(String(siguiente))
  }

  const manejarLayoutLuz = (event: LayoutChangeEvent) => {
    const height = event.nativeEvent.layout.height
    altoControlLuzRef.current = height
    setAltoControlLuz(height)
  }

  const manejarLayoutRiego = (event: LayoutChangeEvent) => {
    const width = event.nativeEvent.layout.width
    anchoControlRiegoRef.current = width
    setAnchoControlRiego(width)
  }

  useEffect(() => {
    intensidadActualRef.current = intensidadActual
  }, [intensidadActual])

  useEffect(() => {
    riegoActualRef.current = riegoActual
  }, [riegoActual])

  const panResponderLuz = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: () => true,
      onPanResponderTerminationRequest: () => false,
      onPanResponderGrant: () => {
        inicioLuzRef.current = intensidadActualRef.current
      },
      onPanResponderMove: (_, gestureState) => {
        if (!altoControlLuzRef.current) {
          return
        }

        const cambio = (-gestureState.dy / altoControlLuzRef.current) * 100
        actualizarLuz(inicioLuzRef.current + cambio)
      },
    })
  ).current

  const panResponderRiego = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: () => true,
      onPanResponderTerminationRequest: () => false,
      onPanResponderGrant: () => {
        inicioRiegoRef.current = riegoActualRef.current
      },
      onPanResponderMove: (_, gestureState) => {
        if (!anchoControlRiegoRef.current) {
          return
        }

        const cambio = (gestureState.dx / anchoControlRiegoRef.current) * MAX_RIEGO_ML
        actualizarRiego(inicioRiegoRef.current + cambio)
      },
    })
  ).current

  const contenidoModal = useMemo(() => {
    const contenido: Record<ClaveModal, { titulo: string; texto: string }> = {
      perfil: {
        titulo: 'Perfil',
        texto: 'Consulta aqui los datos de tu sesion actual.',
      },
      opciones: {
        titulo: 'Opciones',
        texto: 'Desde aqui puedes cerrar sesion jeje.',
      },
      salud: {
        titulo: 'Salud de la planta',
        texto:
          'Aqui puedes revisar el estado general, etapa de crecimiento y alertas.',
      },
      maceta: {
        titulo: 'Maceta',
        texto: 'Informacion fisica actual de la maceta asociada a la planta.',
      },
      tienda: {
        titulo: 'Tienda de macetas',
        texto: 'Elige una maceta para comprarla con tus Plantastic Coins.',
      },
      sustrato: {
        titulo: 'Sustrato',
        texto:
          'Selecciona el sustrato que quieres asignar.',
      },
      historial: {
        titulo: 'Historial de registro',
        texto: 'Aqui se muestran las acciones de cuidado mas recientes.',
      },
      intensidad: {
        titulo: 'Intensidad',
        texto:
          'Ingresa la intensidad de luz entre 0 y 100 para ajustar la lampara.',
      },
      riego: {
        titulo: 'Riego',
        texto:
          'Ingresa la cantidad de agua en ml que quieres aplicar a la planta.',
      },
    }

    return modalActivo ? contenido[modalActivo] : null
  }, [modalActivo])

  const opcionesInferiores: {
    clave: ClaveModal
    imagen: any
  }[] = [
    { clave: 'maceta', imagen: imagenes.maceta },
    { clave: 'sustrato', imagen: imagenes.sustrato },
    { clave: 'historial', imagen: imagenes.historial },
    { clave: 'intensidad', imagen: imagenes.intensidad },
    { clave: 'riego', imagen: imagenes.riego },
  ]

  const indicadores = [
    {
      clave: 'Luz',
      imagen: imagenes.indicadorLuz,
      valor: `${Math.round(planta?.light_level ?? 0)}%`,
    },
    {
      clave: 'Humedad',
      imagen: imagenes.indicadorHumedad,
      valor: `${Math.round(planta?.humidity_level ?? 0)}%`,
    },
    {
      clave: 'Agua',
      imagen: imagenes.indicadorAgua,
      valor: `${Math.round(planta?.water_level ?? 0)}%`,
    },
    {
      clave: 'Sustrato',
      imagen: imagenes.indicadorSustrato,
      valor: planta?.substrate_name || '-',
    },
  ]
  const sustratoSeleccionado =
    sustratos.find(
      (sustrato) => sustrato.id_substrate_type === sustratoSeleccionadoId
    ) || sustratos[0]
  const inventarioMacetas = inventario.filter(
    (item) => item.item_type === 'maceta'
  )
  const idsMacetasCompradas = new Set(
    inventarioMacetas.map((item) => item.id_item)
  )
  const saldoVisible = coinsBalance ?? 0

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.pantalla}>
        <View
          pointerEvents="none"
          style={[styles.luzAmbienteFondo, { opacity: opacidadLuzAmbiente }]}
        />
        <View pointerEvents="none" style={styles.areaConoLuzFondo}>
          <View style={[styles.conoLuzFondo, { opacity: opacidadConoLuz }]} />
        </View>

        <View style={styles.filaSuperior}>
          <Pressable
            style={styles.botonIconoSuperior}
            onPress={() => abrirModal('perfil')}
          >
            <Image source={imagenes.perfil} style={styles.iconoSuperior} />
          </Pressable>

          <View style={styles.indicadores}>
            {indicadores.map((indicador) => (
              <View key={indicador.clave} style={styles.indicadorBloque}>
                <Image source={indicador.imagen} style={styles.iconoIndicador} />
                <Text style={styles.valorIndicador}>{indicador.valor}</Text>
              </View>
            ))}
          </View>

          <Pressable
            style={styles.botonIconoSuperior}
            onPress={() => abrirModal('opciones')}
          >
            <Image source={imagenes.opciones} style={styles.iconoSuperior} />
          </Pressable>
        </View>

        {cargandoPantalla ? (
          <View style={styles.cargandoPantalla}>
            <ActivityIndicator color="#46a11f" size="large" />
            <Text style={styles.textoCargando}>Cargando estado de la planta...</Text>
          </View>
        ) : (
          <>
            <View style={styles.areaCentral}>
              <View style={styles.panelIzquierdo}>
                <Text style={styles.nombrePlanta}>
                  {planta?.plant_name || plantaActual?.nombre || 'Tu planta'}
                </Text>
                <Text style={styles.etapaPlanta}>
                  {formatearEtapa(planta?.growth_stage)}
                </Text>
                <Text style={styles.descripcionEtapa}>
                  {estado?.etapa_descripcion || 'Sin descripcion disponible.'}
                </Text>

                <View style={styles.contenedorPlantaMaceta}>
                  <Animated.Image
                    source={imagenEtapaActual}
                    style={[
                      styles.imagenPlantaConMaceta,
                      {
                        width: layoutEtapa.width,
                        height: layoutEtapa.height,
                        marginBottom: layoutEtapa.marginBottom,
                      },
                      {
                        opacity: planta?.health && planta.health <= 20 ? 0.45 : 0.95,
                        transform: layoutEtapa.centrarImagen
                          ? [{ scale: animacionPlanta }]
                          : [
                              { scale: animacionPlanta },
                              { translateX: layoutEtapa.translateX },
                            ],
                      },
                    ]}
                    resizeMode="contain"
                  />
                </View>

                {feedbackVisual ? (
                  <View style={styles.feedbackVisual}>
                    <Text style={styles.textoFeedback}>{feedbackVisual}</Text>
                  </View>
                ) : null}
              </View>

              <View style={styles.panelDerecho}>
                <Pressable
                  style={styles.botonInfo}
                  onPress={() => abrirModal('salud')}
                >
                  <Image source={imagenes.info} style={styles.iconoInfo} />
                </Pressable>

                <View style={styles.contenedorBarraSalud}>
                  <View style={styles.barraSalud}>
                    <View
                      style={[
                        styles.rellenoSalud,
                        {
                          height: `${clamp(planta?.health ?? 0)}%`,
                          backgroundColor: colorBarra(planta?.health ?? 0),
                        },
                      ]}
                    />
                  </View>
                </View>

                <Text style={styles.textoSalud}>
                  {estado?.salud_etiqueta || 'Sin salud'}
                </Text>

                <Pressable style={styles.botonFlecha} disabled>
                  <Image source={imagenes.flecha} style={styles.iconoFlecha} />
                </Pressable>
              </View>
            </View>

            <View style={styles.filaInferior}>
              {opcionesInferiores.map((opcion) => (
                <Pressable
                  key={opcion.clave}
                  style={styles.botonInferior}
                  onPress={() => abrirModal(opcion.clave)}
                >
                  <Image source={opcion.imagen} style={styles.iconoInferior} />
                </Pressable>
              ))}
            </View>
          </>
        )}
      </View>

      <Modal
        visible={modalActivo !== null}
        transparent
        animationType="fade"
        onRequestClose={cerrarModal}
      >
        <View style={styles.fondoModal}>
          <Pressable style={styles.capaCierre} onPress={cerrarModal} />

          <View style={styles.tarjetaModal}>
            <Text style={styles.tituloModal}>{contenidoModal?.titulo}</Text>

            {modalActivo === 'perfil' ? (
              <View style={styles.contenidoPerfil}>
                <View style={styles.tarjetaPerfil}>
                  <View style={styles.encabezadoPerfil}>
                    <View style={styles.puntoEstado} />
                    <View style={styles.textosPerfil}>
                      <Text style={styles.nombrePerfil}>
                        {usuario?.nombre || 'No disponible'}
                      </Text>
                      <Text style={styles.correoPerfil}>
                        {usuario?.correo || 'No disponible'}
                      </Text>
                    </View>
                  </View>

                  <View style={styles.separadorPerfil} />

                  <View style={styles.filaDato}>
                    <Text style={styles.etiquetaDato}>Numero de plantas:</Text>
                    <Text style={styles.valorDato}>
                      {plantaActual ? '1' : '0'}
                    </Text>
                  </View>

                  <View style={styles.filaDato}>
                    <Text style={styles.etiquetaDato}>Planta activa:</Text>
                    <Text style={styles.valorDato}>
                      {planta?.plant_name || plantaActual?.nombre || 'Sin planta'}
                    </Text>
                  </View>

                  <View style={styles.filaDato}>
                    <Text style={styles.etiquetaDato}>Jardinero desde:</Text>
                    <Text style={styles.valorDato}>{creadoTexto}</Text>
                  </View>

                  <View style={styles.tarjetaMonedasPerfil}>
                    <View>
                      <Text style={styles.etiquetaDato}>Plantastic Coins</Text>
                      <Text style={styles.valorMonedasPerfil}>
                        {saldoVisible} monedas
                      </Text>
                    </View>
                    <Pressable
                      style={styles.botonTiendaPerfil}
                      onPress={() => abrirModal('tienda')}
                    >
                      <Text style={styles.textoBotonTienda}>Tienda</Text>
                    </Pressable>
                  </View>
                </View>
              </View>
            ) : modalActivo === 'opciones' ? (
              <View style={styles.contenidoPerfil}>
                <Text style={styles.textoModal}>{contenidoModal?.texto}</Text>

                {errorModal ? (
                  <Text style={styles.errorPerfil}>{errorModal}</Text>
                ) : null}

                <Pressable
                  style={[
                    styles.botonCerrarSesion,
                    cerrandoSesion && styles.botonCerrarSesionDeshabilitado,
                  ]}
                  onPress={manejarCerrarSesion}
                  disabled={cerrandoSesion}
                >
                  {cerrandoSesion ? (
                    <ActivityIndicator color="#ffffff" />
                  ) : (
                    <Text style={styles.textoCerrarSesion}>Cerrar sesion</Text>
                  )}
                </Pressable>
              </View>
            ) : (
              <ScrollView
                style={styles.scrollModal}
                contentContainerStyle={styles.contenidoModal}
                scrollEnabled={
                  modalActivo !== 'intensidad' && modalActivo !== 'riego'
                }
              >
                <Text style={styles.textoModal}>{contenidoModal?.texto}</Text>

                {cargandoModal ? (
                  <ActivityIndicator color="#46a11f" />
                ) : null}

                {modalActivo === 'salud' ? (
                  <View style={styles.tarjetaPerfil}>
                    <View style={styles.filaDato}>
                      <Text style={styles.etiquetaDato}>Nombre</Text>
                      <Text style={styles.valorDato}>
                        {planta?.plant_name || 'No disponible'}
                      </Text>
                    </View>

                    <View style={styles.filaDato}>
                      <Text style={styles.etiquetaDato}>Etapa</Text>
                      <Text style={styles.valorDato}>
                        {formatearEtapa(planta?.growth_stage)}
                      </Text>
                    </View>

                    <View style={styles.filaDato}>
                      <Text style={styles.etiquetaDato}>Salud</Text>
                      <Text style={styles.valorDato}>
                        {estado?.salud_etiqueta || 'Sin dato'} ({Math.round(planta?.health ?? 0)}%)
                      </Text>
                    </View>

                    <View style={styles.filaDato}>
                      <Text style={styles.etiquetaDato}>Alertas</Text>
                      {estado?.alertas?.length ? (
                        estado.alertas.map((alerta) => (
                          <Text key={alerta} style={styles.alertaTexto}>
                            {alerta}
                          </Text>
                        ))
                      ) : (
                        <Text style={styles.valorDato}>Sin alertas activas.</Text>
                      )}
                    </View>
                  </View>
                ) : null}

                {modalActivo === 'maceta' && maceta ? (
                  <View style={styles.inventarioMaceta}>
                    <View style={styles.encabezadoInventario}>
                      <View>
                        <Text style={styles.tituloInventario}>Tus macetas</Text>
                        <Text style={styles.subtituloInventario}>
                          Inventario disponible para tu planta
                        </Text>
                      </View>

                      <Pressable
                        style={styles.botonTienda}
                        onPress={() => abrirModal('tienda')}
                      >
                        <Text style={styles.textoBotonTienda}>Tienda</Text>
                      </Pressable>
                    </View>

                    <View style={styles.panelInventario}>
                      <ScrollView
                        horizontal
                        showsHorizontalScrollIndicator={false}
                        contentContainerStyle={styles.carruselInventario}
                      >
                        <Pressable
                          style={[
                            styles.slotMaceta,
                            maceta.material === 'plastico' && styles.slotMacetaActiva,
                            ejecutandoAccion && styles.tarjetaSeleccionDeshabilitada,
                          ]}
                          onPress={() =>
                            equiparMaceta('Maceta base', {
                              material: 'plastico',
                              drainage_level: 60,
                              ventilation_level: 50,
                            })
                          }
                          disabled={ejecutandoAccion || maceta.material === 'plastico'}
                        >
                          {maceta.material === 'plastico' ? (
                            <View style={styles.badgeMacetaActiva}>
                              <Text style={styles.textoBadgeMacetaActiva}>Equipada</Text>
                            </View>
                          ) : null}

                          <Image
                            source={imagenes.maceta}
                            style={styles.imagenMacetaInventario}
                            resizeMode="contain"
                          />

                          <Text style={styles.nombreMacetaSlot}>Maceta base</Text>
                          <Text style={styles.materialMacetaSlot}>
                            {maceta.material}
                          </Text>
                        </Pressable>

                        {inventarioMacetas.map((item) => {
                          const preset = obtenerPresetMaceta(item.item_name)
                          const estaEquipada =
                            maceta.material === preset.material &&
                            Math.round(maceta.drainage_level) ===
                              preset.drainage_level &&
                            Math.round(maceta.ventilation_level) ===
                              preset.ventilation_level

                          return (
                            <Pressable
                              key={item.id_inventory}
                              style={[
                                styles.slotMaceta,
                                estaEquipada && styles.slotMacetaActiva,
                                ejecutandoAccion && styles.tarjetaSeleccionDeshabilitada,
                              ]}
                              onPress={() => equiparMaceta(item.item_name, preset)}
                              disabled={ejecutandoAccion || estaEquipada}
                            >
                              {estaEquipada ? (
                                <View style={styles.badgeMacetaActiva}>
                                  <Text style={styles.textoBadgeMacetaActiva}>
                                    Equipada
                                  </Text>
                                </View>
                              ) : null}

                              <Image
                                source={imagenes.maceta}
                                style={styles.imagenMacetaInventario}
                                resizeMode="contain"
                              />
                              <Text style={styles.nombreMacetaSlot}>
                                {item.item_name}
                              </Text>
                              <Text style={styles.materialMacetaSlot}>
                                x{item.quantity}
                              </Text>
                            </Pressable>
                          )
                        })}

                        {inventarioMacetas.length === 0 ? (
                          <View style={styles.slotMacetaVacio}>
                            <Text style={styles.iconoMacetaVacia}>+</Text>
                            <Text style={styles.textoSlotVacio}>
                              {errorInventario
                                ? 'Inventario no disponible'
                                : 'Compra nuevas macetas en la tienda'}
                            </Text>
                          </View>
                        ) : null}
                      </ScrollView>

                      {errorInventario ? (
                        <Text style={styles.avisoInventario}>
                          {errorInventario}
                        </Text>
                      ) : null}

                      <View style={styles.detalleMaceta}>
                        <Text style={styles.nombreMacetaInventario}>
                          Maceta base de {maceta.material}
                        </Text>
                        <Text style={styles.descripcionMacetaInventario}>
                          Esta es tu primera maceta disponible. Las macetas que compres en la tienda apareceran en este inventario.
                        </Text>

                        <View style={styles.gridStatsMaceta}>
                          <View style={styles.statMaceta}>
                            <Text style={styles.labelStatMaceta}>Tamano</Text>
                            <Text style={styles.valorStatMaceta}>{maceta.size_cm} cm</Text>
                          </View>
                          <View style={styles.statMaceta}>
                            <Text style={styles.labelStatMaceta}>Drenaje</Text>
                            <Text style={styles.valorStatMaceta}>
                              {Math.round(maceta.drainage_level)}%
                            </Text>
                          </View>
                          <View style={styles.statMaceta}>
                            <Text style={styles.labelStatMaceta}>Ventilacion</Text>
                            <Text style={styles.valorStatMaceta}>
                              {Math.round(maceta.ventilation_level)}%
                            </Text>
                          </View>
                          <View style={styles.statMaceta}>
                            <Text style={styles.labelStatMaceta}>Material</Text>
                            <Text style={styles.valorStatMaceta}>{maceta.material}</Text>
                          </View>
                        </View>
                      </View>
                    </View>
                  </View>
                ) : null}

                {modalActivo === 'tienda' ? (
                  <View style={styles.tiendaMacetas}>
                    <View style={styles.encabezadoTienda}>
                      <View>
                        <Text style={styles.tituloInventario}>Estanteria</Text>
                        <Text style={styles.subtituloInventario}>
                          Macetas disponibles
                        </Text>
                      </View>

                      <View style={styles.monedaTienda}>
                        <Text style={styles.iconoMoneda}>PC</Text>
                        <Text style={styles.valorMoneda}>{saldoVisible}</Text>
                      </View>
                    </View>

                    <View style={styles.estanteria}>
                      {itemsTienda.map((item) => {
                        const estaComprada = idsMacetasCompradas.has(item.id_item)
                        const saldoInsuficiente = saldoVisible < item.price_coins
                        const comprando = itemComprandoId === item.id_item

                        return (
                          <View key={item.id_item} style={styles.celdaEstanteria}>
                            {estaComprada ? (
                              <View style={styles.badgeMacetaActiva}>
                                <Text style={styles.textoBadgeMacetaActiva}>
                                  Tuya
                                </Text>
                              </View>
                            ) : null}

                            <Image
                              source={imagenes.maceta}
                              style={styles.imagenMacetaTienda}
                              resizeMode="contain"
                            />

                            <View style={styles.repisa} />

                            <Text style={styles.nombreItemTienda}>
                              {item.item_name}
                            </Text>
                            <Text style={styles.rarezaItemTienda}>
                              {item.rarity}
                            </Text>

                            <View style={styles.precioItemTienda}>
                              <Text style={styles.iconoMonedaMini}>PC</Text>
                              <Text style={styles.textoPrecioTienda}>
                                {item.price_coins}
                              </Text>
                            </View>

                            <Pressable
                              style={[
                                styles.botonComprar,
                                (estaComprada ||
                                  saldoInsuficiente ||
                                  itemComprandoId !== null) &&
                                  styles.botonComprarDeshabilitado,
                              ]}
                              onPress={() => comprarMaceta(item)}
                              disabled={
                                estaComprada ||
                                saldoInsuficiente ||
                                itemComprandoId !== null
                              }
                            >
                              {comprando ? (
                                <ActivityIndicator color="#ffffff" size="small" />
                              ) : (
                                <Text style={styles.textoComprar}>
                                  {estaComprada
                                    ? 'Comprada'
                                    : saldoInsuficiente
                                      ? 'Faltan coins'
                                      : 'Comprar'}
                                </Text>
                              )}
                            </Pressable>
                          </View>
                        )
                      })}

                      {!cargandoModal && itemsTienda.length === 0 ? (
                        <Text style={styles.valorDato}>
                          Todavia no hay macetas en la tienda.
                        </Text>
                      ) : null}
                    </View>
                  </View>
                ) : null}

                {modalActivo === 'sustrato' ? (
                  <View style={styles.inventarioMaceta}>
                    <View style={styles.encabezadoInventario}>
                      <View>
                        <Text style={styles.tituloInventario}>Tus sustratos</Text>
                        <Text style={styles.subtituloInventario}>
                          Explora, prueba y elige el que quieras usar
                        </Text>
                      </View>
                    </View>

                    <View style={styles.panelInventario}>
                      <ScrollView
                        horizontal
                        showsHorizontalScrollIndicator={false}
                        contentContainerStyle={styles.carruselInventario}
                      >
                        {sustratos.map((sustrato) => {
                          const estaActivo =
                            planta?.substrate_name?.toLowerCase() ===
                            sustrato.name.toLowerCase()
                          const estaSeleccionado =
                            sustrato.id_substrate_type === sustratoSeleccionadoId

                          return (
                            <Pressable
                              key={sustrato.id_substrate_type}
                              style={[
                                styles.slotMaceta,
                                estaActivo && styles.slotMacetaActiva,
                                estaSeleccionado && styles.slotSustratoSeleccionado,
                                ejecutandoAccion && styles.tarjetaSeleccionDeshabilitada,
                              ]}
                              onPress={() =>
                                setSustratoSeleccionadoId(sustrato.id_substrate_type)
                              }
                              disabled={ejecutandoAccion}
                            >
                              {estaActivo ? (
                                <View style={styles.badgeMacetaActiva}>
                                  <Text style={styles.textoBadgeMacetaActiva}>
                                    Equipado
                                  </Text>
                                </View>
                              ) : null}

                              <View style={styles.iconoSustratoWrap}>
                                <Image
                                  source={imagenes.sustrato}
                                  style={styles.imagenSustratoInventario}
                                  resizeMode="contain"
                                />
                              </View>

                              <Text style={styles.nombreMacetaSlot}>
                                {sustrato.name}
                              </Text>
                              <Text style={styles.materialMacetaSlot}>
                                Sustrato disponible
                              </Text>
                            </Pressable>
                          )
                        })}
                      </ScrollView>

                      {sustratos.length ? (
                        <View style={styles.detalleMaceta}>
                          <Text style={styles.nombreMacetaInventario}>
                            {sustratoSeleccionado?.name || 'Sustrato'}
                          </Text>
                          <Text style={styles.descripcionMacetaInventario}>
                            {descripcionSustratoNeutral(sustratoSeleccionado)}
                          </Text>

                          <View style={styles.gridStatsMaceta}>
                            <View style={styles.statMaceta}>
                              <Text style={styles.labelStatMaceta}>Retencion</Text>
                              <Text style={styles.valorStatMaceta}>
                                {sustratoSeleccionado?.water_retention ?? '-'}
                                x
                              </Text>
                            </View>
                            <View style={styles.statMaceta}>
                              <Text style={styles.labelStatMaceta}>Drenaje</Text>
                              <Text style={styles.valorStatMaceta}>
                                {sustratoSeleccionado?.drainage_factor ?? '-'}
                              </Text>
                            </View>
                            <View style={styles.statMaceta}>
                              <Text style={styles.labelStatMaceta}>Nutrientes</Text>
                              <Text style={styles.valorStatMaceta}>
                                {sustratoSeleccionado?.nutrient_release ?? '-'}
                              </Text>
                            </View>
                            <View style={styles.statMaceta}>
                              <Text style={styles.labelStatMaceta}>Estado</Text>
                              <Text style={styles.valorStatMaceta}>
                                {sustratoSeleccionado?.name?.toLowerCase() ===
                                planta?.substrate_name?.toLowerCase()
                                  ? 'Equipado'
                                  : 'Disponible'}
                              </Text>
                            </View>
                          </View>

                          <Pressable
                            style={[
                              styles.botonAccionPrimaria,
                              (!sustratoSeleccionadoId ||
                                sustratoSeleccionado?.name?.toLowerCase() ===
                                  planta?.substrate_name?.toLowerCase() ||
                                ejecutandoAccion) &&
                                styles.botonCerrarSesionDeshabilitado,
                            ]}
                            onPress={() =>
                              sustratoSeleccionadoId &&
                              aplicarSustrato(sustratoSeleccionadoId)
                            }
                            disabled={
                              !sustratoSeleccionadoId ||
                              sustratoSeleccionado?.name?.toLowerCase() ===
                                planta?.substrate_name?.toLowerCase() ||
                              ejecutandoAccion
                            }
                          >
                            {ejecutandoAccion ? (
                              <ActivityIndicator color="#ffffff" />
                            ) : (
                              <Text style={styles.textoCerrarSesion}>
                                Equipar sustrato
                              </Text>
                            )}
                          </Pressable>
                        </View>
                      ) : null}
                    </View>
                  </View>
                ) : null}

                {modalActivo === 'historial' ? (
                  historial.length ? (
                    <View style={styles.listaHistorial}>
                      {historial.map((item) => (
                        <View key={item.id_history} style={styles.tarjetaHistorial}>
                          <Text style={styles.tituloHistorial}>
                            {formatearAccion(item.action_type)}
                          </Text>
                          <Text style={styles.descripcionHistorial}>
                            {item.extra_info || `Valor registrado: ${item.value}`}
                          </Text>
                          <Text style={styles.metaHistorial}>{item.created_at}</Text>
                        </View>
                      ))}
                    </View>
                  ) : (
                    <Text style={styles.valorDato}>Todavia no hay registros.</Text>
                  )
                ) : null}

                {modalActivo === 'intensidad' ? (
                  <View style={styles.formularioAccion}>
                    <View style={styles.panelLuz}>
                      <View style={styles.encabezadoControl}>
                        <Text style={styles.valorControlGrande}>
                          {intensidadActual}%
                        </Text>
                      <Text style={styles.textoControlSecundario}>
                          Desliza el control o usa los botones para ajustar la intensidad de luz que quieres aplicar a tu planta.
                      </Text>
                      </View>

                      <View style={styles.controlLuzFila}>
                        <Pressable
                          style={styles.botonAjuste}
                          onPress={() => actualizarLuz(intensidadActual - PASO_LUZ)}
                        >
                          <Text style={styles.textoAjuste}>-</Text>
                        </Pressable>

                        <View
                          style={styles.controlLuz}
                          onLayout={manejarLayoutLuz}
                          {...panResponderLuz.panHandlers}
                        >
                          <View style={styles.fondoLuz} />
                          <View
                            style={[
                              styles.rellenoLuz,
                              { height: `${intensidadActual}%` },
                            ]}
                          />
                          <View
                            style={[
                              styles.brilloLuz,
                              {
                                opacity: 0.2 + intensidadActual / 125,
                              },
                            ]}
                          />
                          <View
                            style={[
                              styles.mangoLuz,
                              {
                                top: Math.max(0, Math.min(altoControlLuz - 36, posicionMangoLuz)),
                              },
                            ]}
                          />
                        </View>

                        <Pressable
                          style={styles.botonAjuste}
                          onPress={() => actualizarLuz(intensidadActual + PASO_LUZ)}
                        >
                          <Text style={styles.textoAjuste}>+</Text>
                        </Pressable>
                      </View>
                    </View>
                    <Pressable
                      style={[
                        styles.botonAccionPrimaria,
                        ejecutandoAccion && styles.botonCerrarSesionDeshabilitado,
                      ]}
                      onPress={manejarIntensidad}
                      disabled={ejecutandoAccion}
                    >
                      {ejecutandoAccion ? (
                        <ActivityIndicator color="#ffffff" />
                      ) : (
                        <Text style={styles.textoCerrarSesion}>Aplicar intensidad</Text>
                      )}
                    </Pressable>
                  </View>
                ) : null}

                {modalActivo === 'riego' ? (
                  <View style={styles.formularioAccion}>
                    <View style={styles.panelRiego}>
                      <View style={styles.encabezadoControl}>
                        <Text style={styles.valorControlGrande}>
                          {riegoActual} ml
                        </Text>
                      <Text style={styles.textoControlSecundario}>
                          Llena o vacia la regadera antes de confirmar
                      </Text>
                      </View>

                      <View style={styles.regaderaPreview}>
                        <Image source={imagenes.riego} style={styles.iconoRegaderaGrande} />
                        <View style={styles.tanqueRegadera}>
                          <View
                            style={[
                              styles.rellenoRegadera,
                              { width: `${(riegoActual / MAX_RIEGO_ML) * 100}%` },
                            ]}
                          />
                        </View>
                      </View>

                      <View style={styles.controlRiegoFila}>
                        <Pressable
                          style={styles.botonAjusteHorizontal}
                          onPress={() => actualizarRiego(riegoActual - PASO_RIEGO_ML)}
                        >
                          <Text style={styles.textoAjuste}>-</Text>
                        </Pressable>

                        <View
                          style={styles.controlRiego}
                          onLayout={manejarLayoutRiego}
                          {...panResponderRiego.panHandlers}
                        >
                          <View style={styles.fondoRiego} />
                          <View
                            style={[
                              styles.rellenoRiego,
                              { width: anchoRellenoRiego },
                            ]}
                          />
                          <View
                            style={[
                              styles.mangoRiego,
                              {
                                left: Math.max(
                                  0,
                                  Math.min(anchoControlRiego - 24, posicionMangoRiego)
                                ),
                              },
                            ]}
                          />
                        </View>

                        <Pressable
                          style={styles.botonAjusteHorizontal}
                          onPress={() => actualizarRiego(riegoActual + PASO_RIEGO_ML)}
                        >
                          <Text style={styles.textoAjuste}>+</Text>
                        </Pressable>
                      </View>

                      <View style={styles.escalaRiego}>
                        <Text style={styles.textoEscala}>0 ml</Text>
                        <Text style={styles.textoEscala}>{MAX_RIEGO_ML} ml</Text>
                      </View>
                    </View>
                    <Pressable
                      style={[
                        styles.botonAccionPrimaria,
                        ejecutandoAccion && styles.botonCerrarSesionDeshabilitado,
                      ]}
                      onPress={manejarRiego}
                      disabled={ejecutandoAccion}
                    >
                      {ejecutandoAccion ? (
                        <ActivityIndicator color="#ffffff" />
                      ) : (
                        <Text style={styles.textoCerrarSesion}>Regar ahora</Text>
                      )}
                    </Pressable>
                  </View>
                ) : null}

                {errorModal ? <Text style={styles.errorPerfil}>{errorModal}</Text> : null}
              </ScrollView>
            )}

            <Pressable style={styles.botonCerrar} onPress={cerrarModal}>
              <Text style={styles.textoCerrar}>Cerrar</Text>
            </Pressable>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#050505',
  },
  pantalla: {
    flex: 1,
    paddingHorizontal: 18,
    paddingTop: 12,
    paddingBottom: 22,
    backgroundColor: '#050505',
    overflow: 'hidden',
  },
  luzAmbienteFondo: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: '#f1d36f',
    zIndex: 0,
  },
  areaConoLuzFondo: {
    position: 'absolute',
    top: 64,
    bottom: 92,
    left: 0,
    right: 0,
    overflow: 'hidden',
    zIndex: 0,
  },
  conoLuzFondo: {
    position: 'absolute',
    top: 0,
    left: '50%',
    width: 0,
    height: 0,
    marginLeft: -265,
    borderLeftWidth: 265,
    borderRightWidth: 265,
    borderBottomWidth: 720,
    borderLeftColor: 'transparent',
    borderRightColor: 'transparent',
    borderBottomColor: '#fff0a8',
  },
  filaSuperior: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    minHeight: 64,
    zIndex: 1,
  },
  botonIconoSuperior: {
    width: 52,
    height: 52,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconoSuperior: {
    width: 42,
    height: 42,
    resizeMode: 'contain',
  },
  iconoMoneda: {
    color: '#2a2106',
    backgroundColor: '#f1c84b',
    borderRadius: 999,
    overflow: 'hidden',
    fontSize: 9,
    fontWeight: '900',
    lineHeight: 18,
    width: 18,
    height: 18,
    textAlign: 'center',
  },
  valorMoneda: {
    color: '#f6e7a3',
    fontSize: 13,
    fontWeight: '800',
  },
  indicadores: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'center',
    flex: 1,
    gap: 14,
    paddingHorizontal: 8,
  },
  indicadorBloque: {
    alignItems: 'center',
    gap: 4,
    minWidth: 48,
  },
  iconoIndicador: {
    width: 30,
    height: 30,
    resizeMode: 'contain',
    opacity: 0.82,
  },
  valorIndicador: {
    color: '#b5b5b5',
    fontSize: 10,
    textAlign: 'center',
  },
  cargandoPantalla: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    zIndex: 1,
  },
  textoCargando: {
    color: '#c9c9c9',
    fontSize: 14,
  },
  areaCentral: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingRight: 4,
    paddingLeft: 6,
    position: 'relative',
    zIndex: 1,
  },
  panelIzquierdo: {
    width: '100%',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 0,
  },
  nombrePlanta: {
    color: '#f5f5f5',
    fontSize: 28,
    fontWeight: '800',
    textAlign: 'center',
    marginBottom: 6,
  },
  etapaPlanta: {
    color: '#8cbf71',
    fontSize: 16,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 10,
  },
  descripcionEtapa: {
    color: '#bdbdbd',
    fontSize: 13,
    lineHeight: 19,
    textAlign: 'center',
    marginBottom: 10,
    maxWidth: 220,
  },
  contenedorPlantaMaceta: {
    width: 280,
    height: 330,
    alignItems: 'center',
    justifyContent: 'flex-end',
    position: 'relative',
  },
  imagenPlantaConMaceta: {
    width: 238,
    height: 286,
  },
  feedbackVisual: {
    marginTop: 12,
    backgroundColor: '#153520',
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 7,
  },
  textoFeedback: {
    color: '#9be38d',
    fontSize: 12,
    fontWeight: '700',
  },
  panelDerecho: {
    position: 'absolute',
    right: 0,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  botonInfo: {
    padding: 2,
  },
  iconoInfo: {
    width: 24,
    height: 24,
    resizeMode: 'contain',
  },
  contenedorBarraSalud: {
    width: 34,
    height: 200,
    padding: 3,
    borderWidth: 1,
    borderColor: '#1a1a1a',
    backgroundColor: '#101010',
  },
  barraSalud: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: '#1b1b1b',
  },
  rellenoSalud: {
    backgroundColor: '#46a11f',
  },
  textoSalud: {
    color: '#f3f3f3',
    fontSize: 12,
    textAlign: 'center',
    maxWidth: 70,
  },
  botonFlecha: {
    padding: 4,
    opacity: 0.9,
  },
  iconoFlecha: {
    width: 22,
    height: 22,
    resizeMode: 'contain',
  },
  filaInferior: {
    flexDirection: 'row',
    justifyContent: 'space-evenly',
    alignItems: 'center',
    minHeight: 82,
    paddingHorizontal: 0,
    paddingTop: 12,
    zIndex: 1,
  },
  botonInferior: {
    width: 58,
    height: 58,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconoInferior: {
    width: 42,
    height: 42,
    resizeMode: 'contain',
  },
  fondoModal: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  capaCierre: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.55)',
  },
  tarjetaModal: {
    width: '100%',
    maxWidth: 360,
    maxHeight: '82%',
    backgroundColor: '#141414',
    borderRadius: 18,
    padding: 22,
    borderWidth: 1,
    borderColor: '#2f2f2f',
  },
  scrollModal: {
    maxHeight: 440,
  },
  contenidoModal: {
    gap: 14,
    marginBottom: 18,
  },
  tituloModal: {
    color: '#ffffff',
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 10,
  },
  textoModal: {
    color: '#d7d7d7',
    fontSize: 15,
    lineHeight: 22,
  },
  contenidoPerfil: {
    gap: 14,
    marginBottom: 18,
  },
  tarjetaPerfil: {
    borderRadius: 14,
    backgroundColor: '#1b1b1b',
    borderWidth: 1,
    borderColor: '#2b2b2b',
    padding: 16,
    gap: 14,
  },
  encabezadoPerfil: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  puntoEstado: {
    width: 12,
    height: 12,
    borderRadius: 999,
    backgroundColor: '#46a11f',
    shadowColor: '#46a11f',
    shadowOpacity: 0.4,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 0 },
  },
  textosPerfil: {
    flex: 1,
    gap: 3,
  },
  nombrePerfil: {
    color: '#f3f3f3',
    fontSize: 22,
    fontWeight: '700',
    lineHeight: 28,
  },
  correoPerfil: {
    color: '#bdbdbd',
    fontSize: 14,
    lineHeight: 20,
  },
  separadorPerfil: {
    height: 1,
    backgroundColor: '#2b2b2b',
  },
  filaDato: {
    gap: 4,
  },
  etiquetaDato: {
    color: '#8cbf71',
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  valorDato: {
    color: '#f3f3f3',
    fontSize: 15,
    lineHeight: 21,
  },
  tarjetaMonedasPerfil: {
    borderRadius: 14,
    backgroundColor: '#241f12',
    borderWidth: 1,
    borderColor: '#4a3c17',
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
  },
  valorMonedasPerfil: {
    color: '#f6e7a3',
    fontSize: 20,
    fontWeight: '800',
    marginTop: 4,
  },
  botonTiendaPerfil: {
    backgroundColor: '#8cbf71',
    paddingHorizontal: 13,
    paddingVertical: 9,
    borderRadius: 999,
  },
  alertaTexto: {
    color: '#ff9a9a',
    fontSize: 14,
    lineHeight: 20,
  },
  errorPerfil: {
    color: '#ff8f8f',
    fontSize: 14,
  },
  botonCerrarSesion: {
    backgroundColor: '#b63838',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 46,
  },
  botonAccionPrimaria: {
    backgroundColor: '#46a11f',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 46,
  },
  botonCerrarSesionDeshabilitado: {
    opacity: 0.7,
  },
  textoCerrarSesion: {
    color: '#ffffff',
    fontWeight: '700',
    fontSize: 15,
  },
  botonCerrar: {
    alignSelf: 'flex-end',
    backgroundColor: '#46a11f',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 10,
  },
  textoCerrar: {
    color: '#ffffff',
    fontWeight: '700',
    fontSize: 14,
  },
  listaSustratos: {
    gap: 10,
  },
  inventarioMaceta: {
    gap: 14,
  },
  encabezadoInventario: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: 12,
  },
  tituloInventario: {
    color: '#f3f3f3',
    fontSize: 18,
    fontWeight: '700',
  },
  subtituloInventario: {
    color: '#9e9e9e',
    fontSize: 12,
    marginTop: 2,
  },
  botonTienda: {
    backgroundColor: '#8cbf71',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 999,
  },
  textoBotonTienda: {
    color: '#0d140a',
    fontSize: 12,
    fontWeight: '800',
  },
  tiendaMacetas: {
    gap: 14,
  },
  encabezadoTienda: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 12,
  },
  monedaTienda: {
    borderRadius: 999,
    backgroundColor: '#241f12',
    borderWidth: 1,
    borderColor: '#4a3c17',
    paddingHorizontal: 10,
    paddingVertical: 8,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
  },
  estanteria: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    justifyContent: 'space-between',
  },
  celdaEstanteria: {
    width: '48%',
    minHeight: 218,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#3a2d1d',
    backgroundColor: '#1b1510',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingTop: 12,
    paddingBottom: 10,
    position: 'relative',
    overflow: 'hidden',
  },
  repisa: {
    width: '112%',
    height: 10,
    backgroundColor: '#5a3a22',
    borderTopWidth: 1,
    borderTopColor: '#7a5534',
    borderBottomWidth: 2,
    borderBottomColor: '#2f1d12',
    marginTop: -8,
    marginBottom: 12,
  },
  imagenMacetaTienda: {
    width: 76,
    height: 76,
    marginTop: 8,
    marginBottom: 0,
    zIndex: 1,
  },
  nombreItemTienda: {
    color: '#f3f3f3',
    fontSize: 13,
    fontWeight: '800',
    textAlign: 'center',
    lineHeight: 17,
    minHeight: 36,
  },
  rarezaItemTienda: {
    color: '#8cbf71',
    fontSize: 10,
    textTransform: 'uppercase',
    fontWeight: '700',
    marginTop: 2,
  },
  precioItemTienda: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    marginTop: 8,
    marginBottom: 8,
  },
  iconoMonedaMini: {
    color: '#2a2106',
    backgroundColor: '#f1c84b',
    borderRadius: 999,
    overflow: 'hidden',
    fontSize: 8,
    fontWeight: '900',
    lineHeight: 16,
    width: 16,
    height: 16,
    textAlign: 'center',
  },
  textoPrecioTienda: {
    color: '#f6e7a3',
    fontSize: 13,
    fontWeight: '800',
  },
  botonComprar: {
    marginTop: 'auto',
    backgroundColor: '#46a11f',
    borderRadius: 9,
    minHeight: 36,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 10,
    alignSelf: 'stretch',
  },
  botonComprarDeshabilitado: {
    opacity: 0.62,
  },
  textoComprar: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '800',
    textAlign: 'center',
  },
  panelInventario: {
    gap: 14,
  },
  carruselInventario: {
    gap: 10,
    paddingRight: 6,
  },
  slotMaceta: {
    width: 138,
    minHeight: 132,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#2f2f2f',
    backgroundColor: '#1b1b1b',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 10,
    paddingVertical: 12,
    position: 'relative',
  },
  slotMacetaActiva: {
    borderColor: '#8cbf71',
    backgroundColor: '#1f261b',
  },
  slotSustratoSeleccionado: {
    borderColor: '#4d6fbd',
    backgroundColor: '#1a2030',
  },
  badgeMacetaActiva: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: '#8cbf71',
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 4,
    zIndex: 3,
    elevation: 3,
  },
  textoBadgeMacetaActiva: {
    color: '#0d140a',
    fontSize: 10,
    fontWeight: '800',
  },
  slotMacetaVacio: {
    width: 138,
    minHeight: 132,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#2b2b2b',
    borderStyle: 'dashed',
    backgroundColor: '#151515',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 10,
    paddingVertical: 12,
    gap: 6,
  },
  iconoMacetaVacia: {
    color: '#616161',
    fontSize: 28,
    lineHeight: 30,
  },
  textoSlotVacio: {
    color: '#777777',
    fontSize: 11,
    textAlign: 'center',
  },
  avisoInventario: {
    color: '#d8a45f',
    fontSize: 12,
    lineHeight: 17,
    textAlign: 'center',
  },
  imagenMacetaInventario: {
    width: 70,
    height: 70,
    marginBottom: 8,
  },
  iconoSustratoWrap: {
    width: 70,
    height: 70,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  imagenSustratoInventario: {
    width: 58,
    height: 58,
  },
  nombreMacetaSlot: {
    color: '#f3f3f3',
    fontSize: 14,
    fontWeight: '700',
    textAlign: 'center',
  },
  materialMacetaSlot: {
    color: '#8cbf71',
    fontSize: 11,
    textTransform: 'capitalize',
    marginTop: 2,
  },
  detalleMaceta: {
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#2f2f2f',
    backgroundColor: '#1b1b1b',
    padding: 14,
    gap: 12,
  },
  nombreMacetaInventario: {
    color: '#f3f3f3',
    fontSize: 17,
    fontWeight: '700',
  },
  descripcionMacetaInventario: {
    color: '#c9c9c9',
    fontSize: 13,
    lineHeight: 19,
  },
  tarjetaSeleccion: {
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#2f2f2f',
    backgroundColor: '#1b1b1b',
    padding: 14,
    gap: 6,
  },
  tarjetaSeleccionDeshabilitada: {
    opacity: 0.7,
  },
  tituloSeleccion: {
    color: '#f3f3f3',
    fontSize: 16,
    fontWeight: '700',
  },
  descripcionSeleccion: {
    color: '#c9c9c9',
    fontSize: 13,
    lineHeight: 18,
  },
  metaSeleccion: {
    color: '#8cbf71',
    fontSize: 12,
  },
  gridStatsMaceta: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: 10,
  },
  statMaceta: {
    width: '48%',
    borderRadius: 12,
    backgroundColor: '#141414',
    paddingHorizontal: 10,
    paddingVertical: 10,
    gap: 4,
  },
  labelStatMaceta: {
    color: '#8cbf71',
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  valorStatMaceta: {
    color: '#f3f3f3',
    fontSize: 14,
    fontWeight: '700',
    textTransform: 'capitalize',
  },
  listaHistorial: {
    gap: 10,
  },
  tarjetaHistorial: {
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#2f2f2f',
    backgroundColor: '#1b1b1b',
    padding: 14,
    gap: 6,
  },
  tituloHistorial: {
    color: '#f3f3f3',
    fontSize: 15,
    fontWeight: '700',
  },
  descripcionHistorial: {
    color: '#d0d0d0',
    fontSize: 13,
    lineHeight: 18,
  },
  metaHistorial: {
    color: '#8cbf71',
    fontSize: 11,
  },
  formularioAccion: {
    gap: 12,
  },
  panelLuz: {
    gap: 16,
  },
  encabezadoControl: {
    alignItems: 'center',
    gap: 4,
  },
  valorControlGrande: {
    color: '#f3f3f3',
    fontSize: 28,
    fontWeight: '800',
  },
  textoControlSecundario: {
    color: '#a8a8a8',
    fontSize: 12,
    textAlign: 'center',
  },
  controlLuzFila: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
  },
  controlLuz: {
    width: 72,
    height: 220,
    borderRadius: 999,
    overflow: 'hidden',
    justifyContent: 'flex-end',
    alignItems: 'center',
    position: 'relative',
  },
  fondoLuz: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: '#242424',
    borderRadius: 999,
    borderWidth: 1,
    borderColor: '#323232',
  },
  rellenoLuz: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: '#f6e27f',
  },
  brilloLuz: {
    position: 'absolute',
    top: -16,
    width: 110,
    height: 110,
    borderRadius: 999,
    backgroundColor: '#f6e27f',
  },
  mangoLuz: {
    position: 'absolute',
    width: 84,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#f3f3f3',
    borderWidth: 3,
    borderColor: '#141414',
  },
  botonAjuste: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: '#1f1f1f',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#343434',
  },
  textoAjuste: {
    color: '#ffffff',
    fontSize: 22,
    fontWeight: '700',
    lineHeight: 24,
  },
  panelRiego: {
    gap: 14,
  },
  regaderaPreview: {
    alignItems: 'center',
    gap: 12,
  },
  iconoRegaderaGrande: {
    width: 72,
    height: 72,
    resizeMode: 'contain',
  },
  tanqueRegadera: {
    width: '100%',
    height: 18,
    borderRadius: 999,
    backgroundColor: '#1f2730',
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#314354',
  },
  rellenoRegadera: {
    height: '100%',
    borderRadius: 999,
    backgroundColor: '#57b7ff',
  },
  controlRiegoFila: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  botonAjusteHorizontal: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#1f1f1f',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#343434',
  },
  controlRiego: {
    flex: 1,
    height: 48,
    justifyContent: 'center',
    position: 'relative',
  },
  fondoRiego: {
    height: 18,
    borderRadius: 999,
    backgroundColor: '#1f2730',
    borderWidth: 1,
    borderColor: '#314354',
  },
  rellenoRiego: {
    position: 'absolute',
    left: 0,
    top: 15,
    height: 18,
    borderRadius: 999,
    backgroundColor: '#57b7ff',
  },
  mangoRiego: {
    position: 'absolute',
    top: 9,
    width: 24,
    height: 30,
    borderRadius: 12,
    backgroundColor: '#dff3ff',
    borderWidth: 2,
    borderColor: '#2d5f88',
  },
  escalaRiego: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  textoEscala: {
    color: '#8fb8d9',
    fontSize: 11,
  },
})
