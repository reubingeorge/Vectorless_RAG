import { NextRequest, NextResponse } from 'next/server'

// Use Docker service name for server-side requests
const API_BASE_URL = process.env.API_INTERNAL_URL || 'http://api-gateway:8000'

export async function GET() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/settings/tree`)
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Failed to fetch tree settings:', error)
    return NextResponse.json({
      toc_check_page_num: 20,
      max_page_num_each_node: 10,
      max_token_num_each_node: 20000,
      min_node_pages: 2,
      max_tree_depth: 5,
      max_retry: 3,
      if_add_node_id: true,
      if_add_node_summary: false,
      if_add_doc_description: false,
      if_add_node_text: false,
      if_use_toc: true,
      if_use_ocr: false,
    }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const response = await fetch(`${API_BASE_URL}/api/settings/tree`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Failed to save tree settings:', error)
    return NextResponse.json({ success: false, message: 'Failed to save tree settings' }, { status: 500 })
  }
}
