import { Redirect } from 'expo-router'

import { useSession } from '@/context/session'

export default function Index() {
  const { plantaActual, usuario } = useSession()

  if (!usuario) {
    return <Redirect href="/login" />
  }

  if (!plantaActual) {
    return <Redirect href="/select-plant" />
  }

  return <Redirect href="/(tabs)/home" />
}
