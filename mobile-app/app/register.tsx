import { Link, router } from 'expo-router'
import React, { useState, useEffect } from 'react'
import {
  Alert,
  Image,
  SafeAreaView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native'
import { useFonts } from 'expo-font'
import * as SplashScreen from 'expo-splash-screen'

export default function RegisterScreen() {
  const [nombre, setNombre] = useState('')
  const [correo, setCorreo] = useState('')
  const [confirmarCorreo, setConfirmarCorreo] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [confirmarContrasena, setConfirmarContrasena] = useState('')
  const [mensajeError, setMensajeError] = useState('')

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

  const manejarRegistro = async () => {
    const correoLimpio = correo.trim().toLowerCase()
    const confirmarCorreoLimpio = confirmarCorreo.trim().toLowerCase()
    const nombreLimpio = nombre.trim()

    const formatoCorreo = /\S+@\S+\.\S+/

    if (
      nombreLimpio === '' ||
      correo.trim() === '' ||
      confirmarCorreo.trim() === '' ||
      contrasena.trim() === '' ||
      confirmarContrasena.trim() === ''
    ) {
      setMensajeError('Por favor completa todos los campos')
      return
    }

    if (
      !formatoCorreo.test(correoLimpio) ||
      !formatoCorreo.test(confirmarCorreoLimpio)
    ) {
      setMensajeError('Ingresa un correo válido')
      return
    }

    if (contrasena.length < 8 || confirmarContrasena.length < 8) {
      setMensajeError('La contraseña debe tener mínimo 8 caracteres')
      return
    }

    if (correoLimpio !== confirmarCorreoLimpio) {
      setMensajeError('Los correos no coinciden')
      return
    }

    if (contrasena !== confirmarContrasena) {
      setMensajeError('Las contraseñas no coinciden')
      return
    }

    try {
      setMensajeError('')

      const respuesta = await fetch(
        'https://nine-schools-win.loca.lt//auth/register',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            nombre: nombreLimpio,
            correo: correoLimpio,
            password: contrasena,
          }),
        }
      )

      const textoRespuesta = await respuesta.text()

      let data: any = {}

      try {
        data = JSON.parse(textoRespuesta)
      } catch {
        data = {}
      }

      if (!respuesta.ok) {
        setMensajeError(
          data.mensaje ||
            data.detail ||
            'No se pudo registrar el usuario'
        )
        return
      }

      setNombre('')
      setCorreo('')
      setConfirmarCorreo('')
      setContrasena('')
      setConfirmarContrasena('')
      setMensajeError('')

      Alert.alert(
        'Registro exitoso',
        data.mensaje || data.detail || 'Usuario registrado correctamente',
        [
          {
            text: 'OK',
            onPress: () => router.replace('/login'),
          },
        ]
      )
    } catch (error: any) {
      setMensajeError('No se pudo conectar con el servidor')
    }
  }

  return (
    <SafeAreaView style={styles.container}>
        <Image
        source={require('../assets/images/pozo.png')}
        style={styles.imagenRegister}
        resizeMode="contain"
        />
      <View style={styles.card}>
        <Text style={styles.title}>CREAR CUENTA</Text>

        <View style={styles.fieldGroup}>
          <TextInput
            style={styles.input}
            placeholder="Nombre de usuario"
            placeholderTextColor="#7a7a7a"
            value={nombre}
            onChangeText={setNombre}
          />
        </View>

        <View style={styles.fieldGroup}>
          <TextInput
            style={styles.input}
            placeholder="Correo"
            placeholderTextColor="#7a7a7a"
            keyboardType="email-address"
            autoCapitalize="none"
            value={correo}
            onChangeText={setCorreo}
          />
        </View>

        <View style={styles.fieldGroup}>
          <TextInput
            style={styles.input}
            placeholder="Confirmar correo"
            placeholderTextColor="#7a7a7a"
            keyboardType="email-address"
            autoCapitalize="none"
            value={confirmarCorreo}
            onChangeText={setConfirmarCorreo}
          />
        </View>

        <View style={styles.fieldGroup}>
          <TextInput
            style={styles.input}
            placeholder="Contraseña"
            placeholderTextColor="#7a7a7a"
            secureTextEntry
            value={contrasena}
            onChangeText={setContrasena}
          />
        </View>

        <View style={styles.fieldGroup}>
          <TextInput
            style={styles.input}
            placeholder="Confirmar contraseña"
            placeholderTextColor="#7a7a7a"
            secureTextEntry
            value={confirmarContrasena}
            onChangeText={setConfirmarContrasena}
          />
        </View>

        <Text style={styles.errorText}>{mensajeError}</Text>

        <TouchableOpacity style={styles.button} onPress={manejarRegistro}>
          <Text style={styles.buttonText}>Registrarse</Text>
        </TouchableOpacity>

        <View style={styles.footer}>
          <Text style={styles.footerText}>¿Ya tienes cuenta? </Text>
          <Link href="/login" style={styles.footerLink}>
            Inicia sesión
          </Link>
        </View>
      </View>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#BEA1F7',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  card: {
    width: '100%',
    maxWidth: 400,
    backgroundColor: 'rgba(255, 255, 255, 0)',
    borderRadius: 20,
    padding: 24,
    zIndex: 2,
  },
  title: {
    fontSize: 45,
    fontFamily: 'superplants',
    fontWeight: 'bold',
    color: '#000000',
    textAlign: 'center',
    marginBottom: 24,
  },
  fieldGroup: {
    marginBottom: 14,
  },
  input: {
    backgroundColor: '#dcfcd3',
    borderRadius: 25,
    fontFamily: 'sunshine',
    paddingHorizontal: 12,
    paddingVertical: 12,
    fontSize: 17,
  },
  errorText: {
    minHeight: 20,
    color: '#7a0c0c',
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 10,
  },
  button: {
    backgroundColor: '#81b71a',
    borderRadius: 25,
    paddingVertical: 14,
    alignItems: 'center',
    width: 150,
    alignSelf: 'center',
    marginTop: 6,
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'normal',
    fontFamily: 'superplants',
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 16,
  },
  footerText: {
    color: '#5b3a29',
    fontSize: 14,
  },
  footerLink: {
    color: '#5b3a29',
    fontSize: 14,
    fontWeight: 'bold',
  },
  imagenRegister: {
  position: 'absolute',
  alignSelf: 'center',
  bottom: -100,
  width: 520,
  height: 360,
  opacity: 0.95,
  },
})