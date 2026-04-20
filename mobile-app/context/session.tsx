import React, { createContext, useContext, useMemo, useState } from 'react'

export type UsuarioSesion = {
  id: number
  nombre: string
  correo: string
  online: boolean
  rol_admin: boolean
  creado: string | null
}

type SessionContextType = {
  usuario: UsuarioSesion | null
  setUsuario: (usuario: UsuarioSesion | null) => void
  cerrarSesionLocal: () => void
}

const SessionContext = createContext<SessionContextType | undefined>(undefined)

export function SessionProvider({ children }: React.PropsWithChildren) {
  const [usuario, setUsuario] = useState<UsuarioSesion | null>(null)

  const value = useMemo(
    () => ({
      usuario,
      setUsuario,
      cerrarSesionLocal: () => setUsuario(null),
    }),
    [usuario]
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
