export function Footer() {
  return (
    <footer className="border-t border-surface-light bg-surface/80 backdrop-blur-sm mt-auto py-6 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between text-sm text-text-secondary">
          <p>© 2024 InterviewMind AI. All rights reserved.</p>
          <div className="flex items-center gap-4">
            <a href="#" className="hover:text-primary transition-colors">Privacy</a>
            <a href="#" className="hover:text-primary transition-colors">Terms</a>
            <a href="#" className="hover:text-primary transition-colors">Contact</a>
          </div>
        </div>
      </div>
    </footer>
  )
}
