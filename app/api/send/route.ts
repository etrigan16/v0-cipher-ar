import { NextResponse } from 'next/server';
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

// 1. Le definimos a TypeScript una estructura estricta para los datos que llegan
interface EmailRequestBody {
  nombre: string;
  email: string;
  empresa: string;
  desafio: string;
  descripcion: string;
}

export async function POST(request: Request) {
  try {
    // 2. Le aclaramos que el JSON que viene de la web cumple con esa estructura
    const body = (await request.json()) as EmailRequestBody;
    const { nombre, email, empresa, desafio, descripcion } = body;

    // Validación perimetral básica para que TypeScript sepa que no están vacíos
    if (!nombre || !email || !desafio || !descripcion) {
      return NextResponse.json({ error: 'Faltan campos obligatorios' }, { status: 400 });
    }

    const data = await resend.emails.send({
      from: 'Aukalabs <contacto@aukalabs.com>', // Tu dominio verificado en Resend
      to: 'guillermofernandez16@gmail.com', // Poné acá tu Gmail real donde querés la alerta
      subject: `🚨 Nuevo Contacto desde Aukalabs: ${empresa}`,
      html: `
        <div style="font-family:sans-serif; background:#000; color:#fff; padding:20px; border:1px solid #1a1a1a;">
          <h2 style="color:#00ff99; border-bottom:1px solid #222; padding-bottom:10px;">// SOLICITUD DE AUDITORÍA</h2>
          <p><strong>Cliente:</strong> ${nombre}</p>
          <p><strong>Email:</strong> ${email}</p>
          <p><strong>Empresa:</strong> ${empresa}</p>
          <p style="color:#00ff99;"><strong>Desafío Técnico:</strong> ${desafio}</p>
          <br />
          <p style="color:#888;"><strong>Descripción del problema:</strong></p>
          <div style="background:#050505; padding:15px; border:1px solid #333;">
            ${descripcion}
          </div>
        </div>
      `
    });

    return NextResponse.json({ success: true, data });
  } catch (error) {
    console.error("Error en el servidor de correo:", error);
    return NextResponse.json({ error: 'Error interno en el servidor' }, { status: 500 });
  }
}
