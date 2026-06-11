import { useEffect } from 'react'
import { Spin } from 'antd'
import HomeHero from '../components/HomeHero'
import OnboardingModal from '../components/OnboardingModal'
import { useGuestStore } from '../stores/guestStore'

export default function HomePage() {
  const { loading, showOnboarding, fetchProfile } = useGuestStore()

  useEffect(() => {
    void fetchProfile()
  }, [fetchProfile])

  if (loading) {
    return (
      <div className="home-loading">
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div className="page-home">
      <OnboardingModal open={showOnboarding} />
      <HomeHero />
    </div>
  )
}
