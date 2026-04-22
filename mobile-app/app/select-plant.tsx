import { useFonts } from 'expo-font'
import { Redirect, router } from 'expo-router'
import React, { useMemo, useState } from 'react'
import {
  ActivityIndicator,
  FlatList,
  Image,
  NativeScrollEvent,
  NativeSyntheticEvent,
  Pressable,
  SafeAreaView,
  StyleSheet,
  Text,
  TextInput,
  View,
  useWindowDimensions,
} from 'react-native'

import { API_BASE_URL } from '@/constants/api'
import { useSession } from '@/context/session'

const OPCIONES_PLANTA = [
  {
    id: 'orquidea',
    nombre: 'Orquidea Phalaenopsis',
    tipo: 'orquidea',
    imagen: require('../assets/images/orchid-select.png'),
  },
]

export default function SelectPlantScreen() {
  const { width } = useWindowDimensions()
  const { plantaActual, setPlantaActual, usuario } = useSession()
  const [indiceActivo, setIndiceActivo] = useState(0)
  const [nombrePlanta, setNombrePlanta] = useState('')
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState('')

  const [fontsLoaded, fontError] = useFonts({
    sunshine: require('../assets/fonts/Comfortaa-Regular.ttf'),
    superplants: require('../assets/fonts/super_plants.ttf'),
  })

  const opcionSeleccionada = OPCIONES_PLANTA[indiceActivo]
  const anchoPagina = useMemo(() => width - 48, [width])
  const anchoTarjeta = useMemo(() => Math.min(anchoPagina, 320), [anchoPagina])

  if (!fontsLoaded && !fontError) {
    return null
  }

  if (!usuario) {
    return <Redirect href="/login" />
  }

  if (plantaActual) {
    return <Redirect href="/(tabs)/home" />
  }

  const manejarScroll = (event: NativeSyntheticEvent<NativeScrollEvent>) => {
    const offsetX = event.nativeEvent.contentOffset.x
    const nuevoIndice = Math.round(offsetX / anchoPagina)

    if (nuevoIndice !== indiceActivo) {
      setIndiceActivo(nuevoIndice)
    }
  }

  const confirmarSeleccion = async () => {
    if (guardando) {
      return
    }

    if (!nombrePlanta.trim()) {
      setError('Escribe un nombre para tu planta')
      return
    }

    setError('')
    setGuardando(true)

    try {
      const respuesta = await fetch(`${API_BASE_URL}/plants`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          nombre: nombrePlanta.trim(),
          tipo: opcionSeleccionada.tipo,
          user_id: usuario.id,
        }),
      })

      const textoRespuesta = await respuesta.text()
      let datos: any = {}

      try {
        datos = JSON.parse(textoRespuesta)
      } catch {
        datos = {}
      }

      if (!respuesta.ok) {
        setError(datos.mensaje || 'No se pudo crear la planta')
        return
      }

      setPlantaActual({
        id: datos.planta.id_plant,
        nombre: datos.planta.plant_name,
        tipo: datos.planta.plant_type,
      })
      router.replace('/(tabs)/home')
    } catch (e) {
      console.log('Error creando planta:', e)
      setError('No se pudo conectar con el servidor')
    } finally {
      setGuardando(false)
    }
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.contenido}>
        <Text style={styles.titulo}>SELECCIONA TU PLANTA</Text>

        <FlatList
          data={OPCIONES_PLANTA}
          keyExtractor={(item) => item.id}
          style={styles.lista}
          horizontal
          pagingEnabled
          showsHorizontalScrollIndicator={false}
          snapToAlignment="center"
          decelerationRate="fast"
          onMomentumScrollEnd={manejarScroll}
          contentContainerStyle={styles.listaContenido}
          renderItem={({ item }) => (
            <View style={[styles.pagina, { width: anchoPagina }]}>
              <View style={[styles.tarjeta, { width: anchoTarjeta }]}>
                <Text style={styles.nombreEspecie}>{item.nombre}</Text>
                <Image
                  source={item.imagen}
                  style={styles.imagenPlanta}
                  resizeMode="contain"
                />
              </View>
            </View>
          )}
        />

        <View style={styles.paginacion}>
          {OPCIONES_PLANTA.map((opcion, indice) => (
            <View
              key={opcion.id}
              style={[
                styles.punto,
                indice === indiceActivo && styles.puntoActivo,
              ]}
            />
          ))}
        </View>

        <TextInput
          style={styles.input}
          placeholder="nombre de la planta"
          placeholderTextColor="#596147"
          value={nombrePlanta}
          onChangeText={setNombrePlanta}
          maxLength={30}
        />

        {error ? <Text style={styles.error}>{error}</Text> : null}

        <Pressable
          style={[
            styles.botonConfirmar,
            guardando && styles.botonConfirmarDeshabilitado,
          ]}
          onPress={confirmarSeleccion}
          disabled={guardando}
        >
          {guardando ? (
            <ActivityIndicator color="#05130a" />
          ) : (
            <Text style={styles.botonTexto}>CONFIRMAR ELECCION</Text>
          )}
        </Pressable>
      </View>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#d5f59b',
  },
  contenido: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 24,
    paddingVertical: 32,
  },
  titulo: {
    fontFamily: 'superplants',
    fontSize: 36,
    color: '#0b1207',
    textAlign: 'center',
    marginBottom: 28,
  },
  listaContenido: {
    alignItems: 'center',
  },
  lista: {
    width: '100%',
    flexGrow: 0,
  },
  pagina: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  tarjeta: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  nombreEspecie: {
    fontFamily: 'sunshine',
    fontSize: 26,
    color: '#0b1207',
    textAlign: 'center',
    marginBottom: 18,
  },
  imagenPlanta: {
    width: 220,
    height: 260,
  },
  paginacion: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 12,
    marginBottom: 22,
  },
  punto: {
    width: 8,
    height: 8,
    borderRadius: 999,
    backgroundColor: 'rgba(11, 18, 7, 0.18)',
  },
  puntoActivo: {
    width: 22,
    backgroundColor: '#0b1207',
  },
  input: {
    width: '100%',
    maxWidth: 280,
    borderBottomWidth: 2,
    borderBottomColor: '#4e5f31',
    paddingBottom: 8,
    paddingHorizontal: 4,
    marginBottom: 18,
    fontFamily: 'sunshine',
    fontSize: 24,
    color: '#243017',
    textAlign: 'center',
    backgroundColor: 'transparent',
  },
  error: {
    color: '#a12626',
    fontSize: 14,
    marginBottom: 14,
    textAlign: 'center',
  },
  botonConfirmar: {
    backgroundColor: '#00d66b',
    borderRadius: 16,
    paddingHorizontal: 22,
    paddingVertical: 14,
    minWidth: 250,
    alignItems: 'center',
    justifyContent: 'center',
  },
  botonConfirmarDeshabilitado: {
    opacity: 0.75,
  },
  botonTexto: {
    fontFamily: 'superplants',
    fontSize: 24,
    color: '#05130a',
    textAlign: 'center',
  },
})
