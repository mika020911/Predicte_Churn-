'use client';

import React from 'react';
import { useAuth } from '@/context/AuthContext';

export default function DashboardPage() {
  const { user, logout } = useAuth();

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">🎉 Bienvenue sur le Dashboard !</h1>
      <p className="mb-4">Félicitations, l'authentification fonctionne à 100%.</p>
      {user && (
        <div className="bg-gray-100 p-4 rounded mb-4">
          <p><strong>Utilisateur :</strong> {user.full_name}</p>
          <p><strong>Email :</strong> {user.email}</p>
          <p><strong>Rôle :</strong> {user.role}</p>
        </div>
      )}
      <button 
        onClick={logout}
        className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
      >
        Se déconnecter
      </button>
    </div>
  );
}
