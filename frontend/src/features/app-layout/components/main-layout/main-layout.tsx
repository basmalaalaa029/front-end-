import Navbar from "../navbar";
import Footer from "../footer";
import { Outlet } from "react-router-dom";

export default function MainLayout() {
    return (
        <>
            <Navbar />
            <main className="min-h-screen bg-gray-50">
                <Outlet />
            </main>
            <Footer />
        </>
    );
}