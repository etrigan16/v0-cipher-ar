// src/app/api/send/route.ts
import { NextResponse } from 'next/server';
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { nombre, email, empresa, desafio, descripcion } = body;

    const data = await resend.emails.send({
      from: 'Cipher.ar <contacto@cipher.ar>', // Tu dominio verificado
      to: 'guillermofernandez16@gmail.com', // Tu Gmail personal
      subject: `🚨 NUEVA CONSULTA TÁCTICA: ${empresa}`,
      html: `<div style="font-family:sans-serif; background:#000; color:#fff; padding:20px;">
              <h2 style="color:#00ff99;">// SOLICITUD DE AUDITORÍA</h2>
              <p><strong>Cliente:</strong> ${nombre}</p>
              <p><strong>Email:</strong> ${email}</p>
              <p><strong>Desafío:</strong> ${desafio}</p>
              <p><strong>Mensaje:</strong> ${descripcion}</p>
            </div>`
    });

    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: 'Error en servidor' }, { status: 500 });
  }
}
