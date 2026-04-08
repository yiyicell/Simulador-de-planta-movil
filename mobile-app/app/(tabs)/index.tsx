import React, { useState } from 'react'
import {
  Alert,
  SafeAreaView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native'

export default function IndexScreen() {
  const [nombre, setNombre] = useState('')
  const [correo, setCorreo] = useState('')
  const [confirmarCorreo, setConfirmarCorreo] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [confirmarContrasena, setConfirmarContrasena] = useState('')
  const [mensajeError, setMensajeError] = useState('')

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
    console.log('Intentando conectar...')

    const respuesta = await fetch(
      'https://dry-waves-work.loca.lt///auth/register',
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

    console.log('Status:', respuesta.status)

    const textoRespuesta = await respuesta.text()
    console.log('Respuesta cruda:', textoRespuesta)

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

    Alert.alert(
      'Registro exitoso',
      data.mensaje || data.detail || 'Usuario registrado correctamente'
    )

    setNombre('')
    setCorreo('')
    setConfirmarCorreo('')
    setContrasena('')
    setConfirmarContrasena('')
    setMensajeError('')
  } catch (error: any) {
    console.log('Error completo:', error)
    console.log('Mensaje:', error?.message)
    setMensajeError('No se pudo conectar con el servidor')
  }
}

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.title}>Crear cuenta</Text>

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
      </View>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#dbeed3',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  card: {
    width: '100%',
    maxWidth: 400,
    backgroundColor: '#7fb069',
    borderRadius: 20,
    padding: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#ffffff',
    textAlign: 'center',
    marginBottom: 24,
  },
  fieldGroup: {
    marginBottom: 14,
  },
  label: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 6,
  },
  input: {
    backgroundColor: '#ffffff',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 12,
    fontSize: 14,
  },
  errorText: {
    minHeight: 20,
    color: '#7a0c0c',
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 10,
  },
  button: {
    backgroundColor: '#4f772d',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 6,
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
})