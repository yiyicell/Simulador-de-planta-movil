import { Link, router } from 'expo-router'
import React, { useState, useEffect } from 'react'
import {
  Image,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native'
import { useFonts } from 'expo-font'
import * as SplashScreen from 'expo-splash-screen'

SplashScreen.preventAutoHideAsync()

export default function LoginScreen() {
  const [correo, setCorreo] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const [fontsLoaded, fontError] = useFonts({
    sunshine: require('../assets/fonts/a_little_sunshine.ttf'),
    superplants: require('../assets/fonts/super_plants.ttf'),
  })

  useEffect(() => {
    if (fontsLoaded || fontError) {
      SplashScreen.hideAsync()
    }
  }, [fontsLoaded, fontError])

  if (!fontsLoaded && !fontError) {
    return null
  }

  const manejarLogin = async () => {
    setError('')

    if (!correo.trim() || !password.trim()) {
      setError('Completa todos los campos')
      return
    }

    const correoValido = /\S+@\S+\.\S+/.test(correo)
    if (!correoValido) {
      setError('Ingresa un correo válido')
      return
    }

    try {
      const respuesta = await fetch('https://nine-schools-win.loca.lt//auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          correo: correo.trim(),
          password: password,
        }),
      })

      const datos = await respuesta.json()

      if (!respuesta.ok || !datos.exito) {
        setError(datos.mensaje || 'No se pudo iniciar sesión')
        return
      }

      console.log('Usuario autenticado:', datos.usuario)
      router.replace('/(tabs)')
    } catch (e) {
      console.log('Error login:', e)
      setError('No se pudo conectar con el servidor')
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.contenedorGeneral}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <Image
        source={require('../assets/images/maceta.png')}
        style={styles.imagenLogin}
        resizeMode="contain"
      />

      <View style={styles.contenedor}>
        <View style={styles.card}>
          <Text style={styles.titulo}>BIENVENIDO</Text>

          <TextInput
            style={styles.input}
            placeholder="Correo"
            value={correo}
            onChangeText={setCorreo}
            keyboardType="email-address"
            autoCapitalize="none"
          />

          <TextInput
            style={styles.input}
            placeholder="Contraseña"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
          />

          {error ? <Text style={styles.error}>{error}</Text> : null}

          <Pressable style={styles.recuperarBoton}>
            <Text style={styles.recuperarTexto}>Recuperar contraseña</Text>
          </Pressable>

          <Pressable style={styles.boton} onPress={manejarLogin}>
            <Text style={styles.botonTexto}>Iniciar sesión</Text>
          </Pressable>

          <View style={styles.footer}>
            <Text style={styles.footerTexto}>¿No tienes cuenta? </Text>
            <Link href="/register" style={styles.footerLink}>
              Regístrate
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
    opacity: 1,
    bottom: -50,
  },
  titulo: {
    fontSize: 50,
    fontFamily: 'superplants',
    fontStyle: 'normal',
    textAlign: 'center',
    marginBottom: 30,
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
  },
  error: {
    color: '#d62828',
    marginBottom: 10,
    fontSize: 14,
  },
  recuperarBoton: {
    alignSelf: 'flex-end',
    marginBottom: 24,
  },
  recuperarTexto: {
    fontSize: 14,
    color: '#3943c6',
    textDecorationLine: 'underline',
  },
  boton: {
    backgroundColor: '#81b71a',
    borderRadius: 25,
    paddingVertical: 14,
    alignItems: 'center',
    marginBottom: 24,
    width: 150,
    alignSelf: 'center',
  },
  botonTexto: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
    fontFamily: 'superplants',
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    bottom: -20,
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
  imagenLogin: {
    position: 'absolute',
    alignSelf: 'center',
    bottom: 90,
    width: 420,
    height: 720,
    opacity: 0.9,
  },
})