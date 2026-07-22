import { InterviewProvider } from './context/InterviewContext'
import { AppRouter } from './router'

function App() {
  return (
    <InterviewProvider>
      <AppRouter />
    </InterviewProvider>
  )
}

export default App
