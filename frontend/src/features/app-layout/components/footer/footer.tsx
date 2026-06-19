import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-300 mt-10">
      <div className="max-w-6xl mx-auto px-4 py-10 grid md:grid-cols-3 gap-8">

        {/* About */}
        <div>
          <h2 className="text-white text-lg font-bold mb-3">CV Builder</h2>
          <p className="text-sm text-gray-400">
            Build professional CVs in minutes using our smart AI-powered platform.
          </p>
        </div>

        {/* Links */}
        <div>
          <h3 className="text-white font-semibold mb-3">Quick Links</h3>
          <div className="flex flex-col gap-2 text-sm">
            <Link to="/" className="hover:text-white">Home</Link>
            <Link to="/dashboard" className="hover:text-white">Dashboard</Link>
            <Link to="/pricing" className="hover:text-white">Pricing</Link>
          </div>
        </div>

        {/* Contact */}
        <div>
          <h3 className="text-white font-semibold mb-3">Contact</h3>
          <p className="text-sm">support@careerpilot.com</p>
          <p className="text-sm mt-1">+20 100 000 0000</p>
        </div>

      </div>

      {/* Bottom bar */}
      <div className="border-t border-gray-700 text-center py-4 text-sm text-gray-500">
        © {new Date().getFullYear()} CV Builder. All rights reserved.
      </div>
    </footer>
  );
}
