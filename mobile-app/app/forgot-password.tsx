import { useFonts } from 'expo-font'
import { Link, router } from 'expo-router'
import React, { useState } from 'react'
import {
  ActivityIndicator,
  Alert,
  Image,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native'

import { API_BASE_URL } from '@/constants/api'

export default function ForgotPasswordScreen() {
  const [correo, setCorreo] = useState('')
  const [token, setToken] = useState('')
  const [nuevaContrasena, setNuevaContrasena] = useState('')
  const [confirmarContrasena, setConfirmarContrasena] = useState('')
  const [pasoToken, setPasoToken] = useState(false)
  const [mensaje, setMensaje] = useState('')
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  const [fontsLoaded, fontError] = useFonts({
    sunshine: require('../assets/fonts/Comfortaa-Regular.ttf'),
    superplants: require('../assets/fonts/super_plants.ttf'),
  })

  if (!fontsLoaded && !fontError) {
    return null
  }

  const obtenerMensajeRespuesta = async (respuesta: Response) => {
    const textoRespuesta = await respuesta.text()
    let datos: any = {}

    try {
      datos = JSON.parse(textoRespuesta)
    } catch {
      datos = {}
    }

    return datos.mensaje || datos.detail || ''
  }

  const validarCorreo = () => {
    const correoLimpio = correo.trim().toLowerCase()

    if (!correoLimpio) {
      setError('Ingresa tu correo')
      return null
    }

    if (!/\S+@\S+\.\S+/.test(correoLimpio)) {
      setError('Ingresa un correo valido')
      return null
    }

    return correoLimpio
  }

  const solicitarToken = async () => {
    if (cargando) {
      return
    }

    setError('')
    setMensaje('')

    const correoLimpio = validarCorreo()
    if (!correoLimpio) {
      return
    }

    setCargando(true)

    try {
      const respuesta = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          correo: correoLimpio,
        }),
      })

      const mensajeRespuesta = await obtenerMensajeRespuesta(respuesta)

      if (!respuesta.ok) {
        setError(mensajeRespuesta || 'No se pudo enviar el token')
        return
      }

      setCorreo(correoLimpio)
      setMensaje(
        mensajeRespuesta || 'Revisa tu correo e ingresa el token recibido'
      )
      setPasoToken(true)
    } catch (e) {
      console.log('Error recuperacion:', e)
      setError('No se pudo conectar con el servidor')
    } finally {
      setCargando(false)
    }
  }

  const restablecerContrasena = async () => {
    if (cargando) {
      return
    }

    setError('')
    setMensaje('')

    const correoLimpio = validarCorreo()
    if (!correoLimpio) {
      return
    }

    if (!token.trim()) {
      setError('Ingresa el token')
      return
    }

    if (!nuevaContrasena.trim() || !confirmarContrasena.trim()) {
      setError('Completa las contrasenas')
      return
    }

    if (nuevaContrasena.length < 8) {
      setError('La contrasena debe tener minimo 8 caracteres')
      return
    }

    if (nuevaContrasena !== confirmarContrasena) {
      setError('Las contrasenas no coinciden')
      return
    }

    setCargando(true)

    try {
      const respuesta = await fetch(`${API_BASE_URL}/auth/reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          correo: correoLimpio,
          token: token.trim(),
          nueva_password: nuevaContrasena,
          confirmar_password: confirmarContrasena,
        }),
      })

      const mensajeRespuesta = await obtenerMensajeRespuesta(respuesta)

      if (!respuesta.ok) {
        setError(mensajeRespuesta || 'No se pudo cambiar la contrasena')
        return
      }

      Alert.alert(
        'Contrasena actualizada',
        mensajeRespuesta || 'Ya puedes iniciar sesion con tu nueva contrasena',
        [
          {
            text: 'OK',
            onPress: () => router.replace('/login'),
          },
        ]
      )
    } catch (e) {
      console.log('Error reset password:', e)
      setError('No se pudo conectar con el servidor')
    } finally {
      setCargando(false)
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.contenedorGeneral}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <Image
        source={require('../assets/images/pozo.png')}
        style={styles.imagenFondo}
        resizeMode="contain"
      />

      <View style={styles.contenedor}>
        <View style={styles.card}>
          <Text style={styles.titulo}>RECUPERAR</Text>

          <TextInput
            style={styles.input}
            placeholder="Correo"
            placeholderTextColor="#7a7a7a"
            value={correo}
            onChangeText={setCorreo}
            keyboardType="email-address"
            autoCapitalize="none"
            editable={!cargando}
          />

          {pasoToken ? (
            <>
              <TextInput
                style={styles.input}
                placeholder="Token"
                placeholderTextColor="#7a7a7a"
                value={token}
                onChangeText={setToken}
                autoCapitalize="none"
                editable={!cargando}
              />

              <TextInput
                style={styles.input}
                placeholder="Nueva contrasena"
                placeholderTextColor="#7a7a7a"
                value={nuevaContrasena}
                onChangeText={setNuevaContrasena}
                secureTextEntry
                editable={!cargando}
              />

              <TextInput
                style={styles.input}
                placeholder="Confirmar contrasena"
                placeholderTextColor="#7a7a7a"
                value={confirmarContrasena}
                onChangeText={setConfirmarContrasena}
                secureTextEntry
                editable={!cargando}
              />
            </>
          ) : null}

          {error ? <Text style={styles.error}>{error}</Text> : null}
          {mensaje ? <Text style={styles.mensaje}>{mensaje}</Text> : null}

          <Pressable
            style={[styles.boton, cargando && styles.botonDeshabilitado]}
            onPress={pasoToken ? restablecerContrasena : solicitarToken}
            disabled={cargando}
          >
            {cargando ? (
              <ActivityIndicator color="#ffffff" />
            ) : (
              <Text style={styles.botonTexto}>
                {pasoToken ? 'Cambiar' : 'Enviar token'}
              </Text>
            )}
          </Pressable>

          {pasoToken ? (
            <Pressable
              style={styles.reenviarBoton}
              onPress={solicitarToken}
              disabled={cargando}
            >
              <Text style={styles.reenviarTexto}>Reenviar token</Text>
            </Pressable>
          ) : null}

          <View style={styles.footer}>
            <Text style={styles.footerTexto}>Ya tienes acceso? </Text>
            <Link href="/login" style={styles.footerLink}>
              Inicia sesion
            </Link>
          </View>
        </View>
      </View>
    </KeyboardAvoidingView>
  )
}

const styles = StyleSheet.create({
  contenedorGeneral: {
    flex: 1,
    backgroundColor: '#BEA1F7',
  },
  contenedor: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 28,
    zIndex: 2,
  },
  card: {
    backgroundColor: 'rgba(255, 255, 255, 0)',
    borderRadius: 24,
    padding: 22,
    bottom: -22,
  },
  titulo: {
    fontSize: 48,
    fontFamily: 'superplants',
    textAlign: 'center',
    marginBottom: 24,
    color: '#0e0805',
  },
  input: {
    borderWidth: 1,
    borderColor: '#f6e9ff',
    borderRadius: 25,
    paddingHorizontal: 14,
    paddingVertical: 12,
    marginBottom: 14,
    fontSize: 16,
    fontFamily: 'sunshine',
    backgroundColor: '#ebf2e5',
    color: '#2f241e',
  },
  error: {
    color: '#7a0c0c',
    marginBottom: 10,
    fontSize: 14,
    textAlign: 'center',
  },
  mensaje: {
    color: '#315f1d',
    marginBottom: 10,
    fontSize: 14,
    lineHeight: 20,
    textAlign: 'center',
  },
  boton: {
    backgroundColor: '#81b71a',
    borderRadius: 25,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 6,
    marginBottom: 16,
    width: 150,
    alignSelf: 'center',
  },
  botonDeshabilitado: {
    opacity: 0.7,
  },
  botonTexto: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
    fontFamily: 'superplants',
  },
  reenviarBoton: {
    alignSelf: 'center',
    marginBottom: 18,
  },
  reenviarTexto: {
    fontSize: 14,
    color: '#3943c6',
    textDecorationLine: 'underline',
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
  },
  footerTexto: {
    fontSize: 14,
    color: '#5b3a29',
  },
  footerLink: {
    fontSize: 14,
    fontWeight: '700',
    color: '#5b3a29',
  },
  imagenFondo: {
    position: 'absolute',
    alignSelf: 'center',
    bottom: -100,
    width: 520,
    height: 360,
    opacity: 0.95,
  },
})
