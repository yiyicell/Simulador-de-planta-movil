import React, { createContext, useContext, useMemo, useState } from 'react'

export type UsuarioSesion = {
  id: number
  nombre: string
  correo: string
  online: boolean
  rol_admin: boolean
  creado: string | null
}

export type PlantaSesion = {
  id: number
  nombre: string
  tipo: string
}

type SessionContextType = {
  usuario: UsuarioSesion | null
  plantaActual: PlantaSesion | null
  setUsuario: (usuario: UsuarioSesion | null) => void
  setPlantaActual: (planta: PlantaSesion | null) => void
  cerrarSesionLocal: () => void
}

const SessionContext = createContext<SessionContextType | undefined>(undefined)

export function SessionProvider({ children }: React.PropsWithChildren) {
  const [usuario, setUsuario] = useState<UsuarioSesion | null>(null)
  const [plantaActual, setPlantaActual] = useState<PlantaSesion | null>(null)

  const value = useMemo(
    () => ({
      usuario,
      plantaActual,
      setUsuario,
      setPlantaActual,
      cerrarSesionLocal: () => {
        setUsuario(null)
        setPlantaActual(null)
      },
    }),
    [plantaActual, usuario]
  )

  return (
    <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
  )
}

export function useSession() {
  const context = useContext(SessionContext)

  if (!context) {
    throw new Error('useSession debe usarse dentro de SessionProvider')
  }

  return context
}
