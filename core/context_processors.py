def currency_context(request):
    """Context processor para agregar información de moneda del usuario"""
    context = {
        'currency_symbol': '$',  # Por defecto
        'currency_code': 'USD',  # Por defecto
        'currency_name': 'Dólar estadounidense',  # Por defecto
    }
    
    if request.user.is_authenticated:
        try:
            print(f"🔍 DEBUG: Usuario autenticado: {request.user}")
            print(f"🔍 DEBUG: hasattr id_moneda: {hasattr(request.user, 'id_moneda')}")
            
            if hasattr(request.user, 'id_moneda'):
                print(f"🔍 DEBUG: id_moneda: {request.user.id_moneda}")
                
                if request.user.id_moneda:
                    moneda = request.user.id_moneda
                    print(f"🔍 DEBUG: Moneda encontrada: {moneda.simbolo} ({moneda.codigo})")
                    context.update({
                        'currency_symbol': moneda.simbolo,
                        'currency_code': moneda.codigo,
                        'currency_name': moneda.nombre,
                    })
                else:
                    print("🔍 DEBUG: id_moneda es None")
            else:
                print("🔍 DEBUG: Usuario no tiene atributo id_moneda")
                
        except Exception as e:
            print(f"❌ DEBUG: Error en context processor: {e}")
            # Si hay error, mantener valores por defecto
    else:
        print("🔍 DEBUG: Usuario no autenticado")
    
    print(f"🔍 DEBUG: Context final: {context}")
    return context
