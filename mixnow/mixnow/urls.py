from django.urls import path
from app import views
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Inicio y cierre de sesión
    path('', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # CRUD de clientes
    path('inicio/', views.inicio, name='inicio'),
    path('clientes/', views.Listar_Clientes.as_view(), name='listar_clientes'),
    path('cliente/crear/', views.Crear_Cliente.as_view(), name='crear_cliente'),
    path('cliente/editar/<int:pk>/', views.Editar_Cliente.as_view(), name='editar_cliente'),
    path('cliente/eliminar/<int:pk>/', views.Eliminar_Cliente.as_view(), name='eliminar_cliente'),
    path('cliente/detalle/<int:pk>/', views.Detalle_Clientes.as_view(), name='detalle_cliente'),

    #COTIZACIONES   
    path('clientes/aridos/<int:cotizacion_id>/', views.CotizacionAridosView.as_view(), name='vista_aridos'),
    path('clientes/valentino/<int:cotizacion_id>/', views.CotizacionValentinoView.as_view(), name='vista_valentino'),
    path('clientes/inverland/<int:cotizacion_id>/', views.CotizacionInverlandView.as_view(), name='vista_inverland'),
    path('clientes/mixnow/<int:cotizacion_id>/', views.CotizacionMixNowView.as_view(), name='vista_mixnow'),
    path('clientes/mixnow_antofagasta/<int:cotizacion_id>/', views.CotizacionMixNowAntofagastaView.as_view(), name='vista_mixnow_antofagasta'),

    path('pdf/<int:cotizacion_id>/<str:plantilla>/', views.descargar_pdf, name='generar_pdf'),
  
    path('instrucciones/', views.instrucciones, name = 'instrucciones'),

    #CRUD de camiones
    path('camiones/', views.Listar_Camiones.as_view(), name='listar_camiones'),
    path('camiones/crear/', views.crear_camion, name='crear_camiones'),
    path('camiones/eliminar/<int:pk>/', views.Eliminar_Camion.as_view(), name='eliminar_camiones'),
    path('camiones/editar/<int:pk>/', views.Actualizar_Camion, name='editar_camiones'),

    #DOCUMENTOS MOSTRAR Y ELIMINAR
    path('camiones/<int:camion_id>/documentos/', views.documentos_camion, name='documentos_camion'),
    path('documento/eliminar/<int:doc_id>/', views.eliminar_documento, name='eliminar_documento'),

    #EMPRESAS
    path('empresas/', views.Listar_Empresa.as_view(), name='listar_empresas'),

    #TRABAJADORES
    path('trabajadores/crear/', views.crear_Trabajador, name='crear_trabajadores'),
    path('trabajadores/<int:empresa_id>/', views.Listar_Trabajadores.as_view(), name='listar_trabajadores'),
    path('trabajadores/editar/<int:pk>/', views.Actualizar_Trabajadores, name='editar_trabajadores'),
    path('trabajadores/eliminar/<int:pk>/', views.Eliminar_Trabajadores, name='eliminar_trabajadores'),
    path('trabajadores/<int:trabajador_id>/documentos/', views.documento_trabajador, name='documentos_trabajador'),
    path('documento_trabajador/eliminar/<int:doc_id>/', views.eliminar_documento_trabajador, name='eliminar_documento_trabajador'),

    #ESTADOS DE PAGO
    path('cliente/detalle_epp/<int:pk>', views.Detalle_Cliente_EDP.as_view(), name='detalle_cliente_epp'),
    path('estado-pago/aridos/<int:estado_id>/', views.EstadoPagoAridosView.as_view(), name='estado_pago_aridos'),
    path('estado-pago/valentino/<int:estado_id>/', views.EstadoPagoValentinoView.as_view(), name='estado_pago_valentino'),
    path('estado-pago/inverland/<int:estado_id>/', views.EstadoInverlandView.as_view(), name='estado_pago_inverland'),
    path('estado-pago/mixnow/<int:estado_id>/', views.EstadoPagoMixNowView.as_view(), name='estado_pago_mixnow'),

    path('pdf-edp/<int:estado_id>/<str:plantilla>/', views.descargar_pdf_edp, name='generar_pdf_edp'),

    path('camiones/fechas/', views.Vencimiento_fechas_camiones.as_view(), name='fechas_camiones'),

    path("historial/", views.HistorialListView.as_view(), name='historial'),


]

#PARA PODER SUBIR ARCHIVOS MEDIA 
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
