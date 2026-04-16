import { router } from 'expo-router'
import React, { useEffect, useMemo, useState } from 'react'
import {
  ActivityIndicator,
  Image,
  Modal,
  Pressable,
  SafeAreaView,
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
  | 'sustrato'
  | 'historial'
  | 'intensidad'
  | 'riego'

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
}

export default function HomeScreen() {
  const [modalActivo, setModalActivo] = useState<ClaveModal | null>(null)
  const [cerrandoSesion, setCerrandoSesion] = useState(false)
  const [errorModal, setErrorModal] = useState('')
  const { usuario, cerrarSesionLocal } = useSession()

  useEffect(() => {
    if (!usuario) {
      router.replace('/login')
    }
  }, [usuario])

  const abrirModal = (clave: ClaveModal) => {
    setErrorModal('')
    setModalActivo(clave)
  }

  const cerrarModal = () => {
    setModalActivo(null)
  }

  const contenidoModal = useMemo(() => {
    const contenido: Record<ClaveModal, { titulo: string; texto: string }> = {
      perfil: {
        titulo: 'Perfil',
        texto: 'Consulta aqui los datos de tu sesion actual.',
      },
      opciones: {
        titulo: 'Opciones',
        texto:
          'Aqui luego podran ir ajustes generales de la app, sonido, ayuda y otras configuraciones.',
      },
      salud: {
        titulo: 'Salud de la planta',
        texto:
          'Esta barra mostrara el estado general de la planta segun sus cuidados y condiciones.',
      },
      maceta: {
        titulo: 'Maceta',
        texto:
          'Aqui luego podras ver o cambiar informacion relacionada con la maceta de la planta.',
      },
      sustrato: {
        titulo: 'Sustrato',
        texto:
          'Aqui luego podras consultar el tipo de sustrato, su estado y posibles recomendaciones.',
      },
      historial: {
        titulo: 'Historial de registro',
        texto:
          'Aqui luego apareceran los registros y eventos guardados sobre el cuidado de la planta.',
      },
      intensidad: {
        titulo: 'Intensidad',
        texto:
          'Aqui luego podras ajustar o consultar la intensidad de luz que recibe la planta.',
      },
      riego: {
        titulo: 'Riego',
        texto:
          'Aqui luego podras registrar el riego o revisar el estado actual del agua.',
      },
    }

    return modalActivo ? contenido[modalActivo] : null
  }, [modalActivo])

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

  const opcionesInferiores: Array<{
    clave: ClaveModal
    imagen: any
  }> = [
    { clave: 'maceta', imagen: imagenes.maceta },
    { clave: 'sustrato', imagen: imagenes.sustrato },
    { clave: 'historial', imagen: imagenes.historial },
    { clave: 'intensidad', imagen: imagenes.intensidad },
    { clave: 'riego', imagen: imagenes.riego },
  ]

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.pantalla}>
        <View style={styles.filaSuperior}>
          <Pressable
            style={styles.botonIconoSuperior}
            onPress={() => abrirModal('perfil')}
          >
            <Image source={imagenes.perfil} style={styles.iconoSuperior} />
          </Pressable>

          <View style={styles.indicadores}>
            <Image
              source={imagenes.indicadorLuz}
              style={styles.iconoIndicador}
            />
            <Image
              source={imagenes.indicadorHumedad}
              style={styles.iconoIndicador}
            />
            <Image
              source={imagenes.indicadorAgua}
              style={styles.iconoIndicador}
            />
            <Image
              source={imagenes.indicadorSustrato}
              style={styles.iconoIndicador}
            />
          </View>

          <Pressable
            style={styles.botonIconoSuperior}
            onPress={() => abrirModal('opciones')}
          >
            <Image source={imagenes.opciones} style={styles.iconoSuperior} />
          </Pressable>
        </View>

        <View style={styles.areaCentral}>
          <View style={styles.panelDerecho}>
            <Pressable
              style={styles.botonInfo}
              onPress={() => abrirModal('salud')}
            >
              <Image source={imagenes.info} style={styles.iconoInfo} />
            </Pressable>

            <View style={styles.contenedorBarraSalud}>
              <View style={styles.barraSalud}>
                <View style={styles.rellenoSalud} />
              </View>
            </View>

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
                    <Text style={styles.valorDato}>0</Text>
                  </View>

                  <View style={styles.filaDato}>
                    <Text style={styles.etiquetaDato}>Jardinero desde:</Text>
                    <Text style={styles.valorDato}>{creadoTexto}</Text>
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
              <Text style={styles.textoModal}>{contenidoModal?.texto}</Text>
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
  },
  filaSuperior: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    minHeight: 64,
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
  indicadores: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
    gap: 16,
    paddingHorizontal: 12,
  },
  iconoIndicador: {
    width: 30,
    height: 30,
    resizeMode: 'contain',
    opacity: 0.72,
  },
  areaCentral: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'flex-end',
    paddingRight: 4,
  },
  panelDerecho: {
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
    height: '82%',
    backgroundColor: '#46a11f',
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
    maxWidth: 340,
    backgroundColor: '#141414',
    borderRadius: 18,
    padding: 22,
    borderWidth: 1,
    borderColor: '#2f2f2f',
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
})
