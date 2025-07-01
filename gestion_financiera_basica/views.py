from django.shortcuts import render, redirect
from .forms import MovimientoForm
from cuentas.models import Cuenta
from django.shortcuts import render
from django.db.models import Sum
from cuentas.models import Cuenta
from .models import Movimiento

def savings_goals(request):
    goals = [
        ("Emergency Fund", "$3000.00 / $5000.00", "60%", "December 30, 2023", "Emergency fund for unexpected expenses"),
        ("Vacation", "$800.00 / $2000.00", "40%", "October 14, 2023", "Summer beach vacation"),
        ("New Laptop", "$450.00 / $1200.00", "37.5%", "November 29, 2023", "Replace old laptop"),
    ]

    tips = [
        ("📂", "50/30/20 Rule", "Allocate 50% of income to needs, 30% to wants, and 20% to savings."),
        ("🌱", "Pay Yourself First", "Transfer money to savings as soon as you receive income."),
    ]

    return render(request, "gestion_financiera_basica/savings_goals.html", {
        "goals": goals,
        "tips": tips
    })

def transactions(request):
    user_id = request.user.id

    filter_type = request.GET.get("filter", "all")

    transacciones = Movimiento.objects.filter(id_cuenta__id_usuario=user_id)
    # egresos = Movimiento.objects.filter(id_cuenta__id_usuario=user_id , tipo="egreso")

    all_transactions = [
        ("Internet Bill", "Jul 21, 2023", "Utilities", "-$150.00", "bg-teal-500"),
        ("Movie Night", "Jul 19, 2023", "Entertainment", "-$35.00", "bg-indigo-500"),
        ("Restaurant Dinner", "Jul 17, 2023", "Food & Dining", "-$60.00", "bg-yellow-500"),
        ("Freelance Work", "Jul 14, 2023", "Income", "+$200.00", "bg-teal-500"),
        ("Gas Bill", "Jul 9, 2023", "Utilities", "-$45.00", "bg-teal-500"),
        ("Grocery Shopping", "Jul 4, 2023", "Food & Dining", "-$120.00", "bg-yellow-500"),
        ("Rent Payment", "Jul 2, 2023", "Housing", "-$800.00", "bg-indigo-500"),
        ("Monthly Salary", "Jun 30, 2023", "Income", "+$2500.00", "bg-teal-500"),
    ]

    if filter_type == "income":
        transactions = [t for t in all_transactions if "+" in t[3]]
    elif filter_type == "expenses":
        transactions = [t for t in all_transactions if "-" in t[3]]
    else:
        transactions = all_transactions

    return render(request, "gestion_financiera_basica/transactions.html", {
        "transactions": all_transactions,
    })
    
def agregar_movimiento(request):
    if request.method == 'POST':
        form = MovimientoForm(request.POST)
        
        if form.is_valid():
            # Guardar el movimiento en la base de datos sin commit
            movimiento = form.save(commit=False)
            tipo = movimiento.tipo  # 'ingreso' o 'egreso'
            monto = movimiento.monto
            id_cuenta = movimiento.id_cuenta  # Obtener la cuenta relacionada

            # Verificar si la cuenta existe
            try:
                cuenta = Cuenta.objects.get(id=id_cuenta.id)
            except Cuenta.DoesNotExist:
                # Si no existe la cuenta, redirigir o mostrar un error
                return redirect('error')  # Cambia esto a la URL o vista que desees para manejo de errores

            # Si el tipo es "ingreso", aumentar el saldo
            if tipo == 'ingreso':
                cuenta.saldo_cuenta += monto  # Aumentar el saldo
            elif tipo == 'egreso':
                cuenta.saldo_cuenta -= monto  # Reducir el saldo
            
            # Verificar que el saldo no sea negativo (si es necesario)
            if cuenta.saldo_cuenta < 0 and tipo == 'egreso':
                form.add_error('monto', 'El saldo no puede ser negativo.')
                return render(request, 'gestion_financiera_basica/add_transaction.html', {'form': form})

            # Guardar la cuenta actualizada
            cuenta.save()

            # Ahora guardar el movimiento
            movimiento.save()

            # Redirigir a la vista de dashboard donde se debe reflejar el cambio
            return redirect('core:dashboard')  # Redirigir al dashboard para ver el saldo actualizado

    else:
        form = MovimientoForm()

    return render(request, 'gestion_financiera_basica/add_transaction.html', {'form': form})