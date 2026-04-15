import React, { useMemo, useState } from 'react'
import {
  Image,
  Modal,
  Pressable,
  SafeAreaView,
  StyleSheet,
  Text,
  View,
} from 'react-native'

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

  const abrirModal = (clave: ClaveModal) => {
    setModalActivo(clave)
  }

  const cerrarModal = () => {
    setModalActivo(null)
  }

  const contenidoModal = useMemo(() => {
    const contenido: Record<ClaveModal, { titulo: string; texto: string }> = {
      perfil: {
        titulo: 'Perfil',
        texto:
          'Aquí luego irá la información del usuario, edición de datos y configuración personal.',
      },
      opciones: {
        titulo: 'Opciones',
        texto:
          'Aquí luego podrán ir ajustes generales de la app, sonido, ayuda y otras configuraciones.',
      },
      salud: {
        titulo: 'Salud de la planta',
        texto:
          'Esta barra mostrará el estado general de la planta según sus cuidados y condiciones.',
      },
      maceta: {
        titulo: 'Maceta',
        texto:
          'Aquí luego podrás ver o cambiar información relacionada con la maceta de la planta.',
      },
      sustrato: {
        titulo: 'Sustrato',
        texto:
          'Aquí luego podrás consultar el tipo de sustrato, su estado y posibles recomendaciones.',
      },
      historial: {
        titulo: 'Historial de registro',
        texto:
          'Aquí luego aparecerán los registros y eventos guardados sobre el cuidado de la planta.',
      },
      intensidad: {
        titulo: 'Intensidad',
        texto:
          'Aquí luego podrás ajustar o consultar la intensidad de luz que recibe la planta.',
      },
      riego: {
        titulo: 'Riego',
        texto:
          'Aquí luego podrás registrar el riego o revisar el estado actual del agua.',
      },
    }

    return modalActivo ? contenido[modalActivo] : null
  }, [modalActivo])

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
            <Text style={styles.textoModal}>{contenidoModal?.texto}</Text>

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
    marginBottom: 18,
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
