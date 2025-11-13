import { NextResponse } from 'next/server'

// Use Docker service name for server-side requests
const API_BASE_URL = process.env.API_INTERNAL_URL || 'http://api-gateway:8000'

export async function GET() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/settings/key-status`)
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Failed to fetch key status:', error)
    return NextResponse.json({ exists: false }, { status: 500 })
  }
}
