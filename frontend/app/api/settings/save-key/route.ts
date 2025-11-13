import { NextRequest, NextResponse } from 'next/server'

// Use Docker service name for server-side requests
const API_BASE_URL = process.env.API_INTERNAL_URL || 'http://api-gateway:8000'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const response = await fetch(`${API_BASE_URL}/api/settings/save-key`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Failed to save key:', error)
    return NextResponse.json({ success: false, message: 'Failed to save key' }, { status: 500 })
  }
}
