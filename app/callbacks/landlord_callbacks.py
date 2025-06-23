from dash import Input, Output, State, no_update
from dash import dcc, html
import plotly.graph_objs as go
from dash import callback_context

def register_landlord_callbacks(app):
    @app.callback(
        Output('landlord-calculator-results', 'children'),
        Output('cash-flow-chart', 'figure'),
        Output('roi-chart', 'figure'),
        Output('landlord-history-dropdown', 'options'),
        Output('landlord-history-dropdown', 'value'),
        Output('landlord-history-store', 'data'),
        Input('calculate-button', 'n_clicks'),
        Input('landlord-history-dropdown', 'value'),
        State('units-input', 'value'),
        State('purchase-price-input', 'value'),
        State('monthly-rent-input', 'value'),
        State('down-payment-slider', 'value'),
        State('mortgage-rate-slider', 'value'),
        State('loan-term-slider', 'value'),
        State('property-tax-slider', 'value'),
        State('maintenance-rate-slider', 'value'),
        State('appreciation-rate-slider', 'value'),
        State('landlord-history-store', 'data'),
        prevent_initial_call=True
    )
    def landlord_combined_callback(n_clicks, selected_idx, units, purchase_price, monthly_rent, down_payment_pct, mortgage_rate, loan_term, property_tax_rate, maintenance_rate, appreciation_rate, history):
        ctx = callback_context
        triggered = ctx.triggered[0]['prop_id'] if ctx.triggered else ''
        years = 5
        # Ensure history is a list
        if not history:
            history = []
        # If Calculate button was pressed, add new entry
        if triggered.startswith('calculate-button'):
            if not all([units, purchase_price, monthly_rent]):
                return '', {}, {}, [{'label': e['label'], 'value': i} for i, e in enumerate(history)], selected_idx, history
            total_purchase_price = units * purchase_price
            down_payment = total_purchase_price * (down_payment_pct / 100)
            loan_amount = total_purchase_price - down_payment
            monthly_rate = mortgage_rate / 100 / 12
            num_payments = loan_term * 12
            if monthly_rate > 0:
                monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
            else:
                monthly_payment = loan_amount / num_payments
            property_tax_monthly = total_purchase_price * (property_tax_rate / 100) / 12
            maintenance_monthly = monthly_rent * units * (maintenance_rate / 100)
            gross_monthly_rent = monthly_rent * units
            total_monthly_expenses = monthly_payment + property_tax_monthly + maintenance_monthly
            net_monthly_cash_flow = gross_monthly_rent - total_monthly_expenses
            annual_rent = gross_monthly_rent * 12
            annual_expenses = total_monthly_expenses * 12
            annual_cash_flow = net_monthly_cash_flow * 12
            cash_on_cash_return = (annual_cash_flow / down_payment) * 100 if down_payment else 0
            cap_rate = (annual_cash_flow / total_purchase_price) * 100 if total_purchase_price else 0
            gross_rent_multiplier = total_purchase_price / annual_rent if annual_rent else 0
            total_appreciation = total_purchase_price * ((1 + appreciation_rate/100)**years - 1)
            total_cash_flow_5yr = annual_cash_flow * years
            total_return_5yr = (total_appreciation + total_cash_flow_5yr) / down_payment * 100 if down_payment else 0
            principal_payment = monthly_payment * (1 - (monthly_rate / (1 + monthly_rate)**num_payments - 1)) if num_payments > 0 else 0
            interest_payment = monthly_payment - principal_payment
            results = f"""
🏠 <b>INVESTMENT OVERVIEW</b><br>======================<br>
Portfolio: {units} rental units<br>
Total Investment: €{total_purchase_price:,.0f}<br>
Your Down Payment: €{down_payment:,.0f} ({down_payment_pct}%)<br>
Mortgage Required: €{loan_amount:,.0f}<br><br>
💰 <b>MONTHLY CASH FLOW ANALYSIS</b><br>=============================<br>
📈 <b>INCOME:</b><br>&nbsp;&nbsp;Gross Monthly Rent: €{gross_monthly_rent:,.0f}<br><br>
📉 <b>EXPENSES:</b><br>&nbsp;&nbsp;Mortgage Payment: €{monthly_payment:,.0f}<br>&nbsp;&nbsp;&nbsp;&nbsp;- Principal: €{principal_payment:,.0f}<br>&nbsp;&nbsp;&nbsp;&nbsp;- Interest: €{interest_payment:,.0f}<br>&nbsp;&nbsp;Property Tax (OZB): €{property_tax_monthly:,.0f}<br>&nbsp;&nbsp;Maintenance & Management: €{maintenance_monthly:,.0f}<br><br>
💵 <b>NET MONTHLY CASH FLOW:</b> €{net_monthly_cash_flow:,.0f}<br><br>
📊 <b>ANNUAL PERFORMANCE METRICS</b><br>=============================<br>
Annual Rental Income: €{annual_rent:,.0f}<br>
Annual Operating Expenses: €{annual_expenses:,.0f}<br>
Annual Cash Flow: €{annual_cash_flow:,.0f}<br><br>
🎯 <b>INVESTMENT RETURNS:</b><br>Cash-on-Cash Return: {cash_on_cash_return:.1f}%<br>&nbsp;&nbsp;(Your annual return on the money you invested)<br>Cap Rate: {cap_rate:.1f}%<br>&nbsp;&nbsp;(Annual return relative to total property value)<br>Gross Rent Multiplier: {gross_rent_multiplier:.1f}x<br>&nbsp;&nbsp;(Years to pay off property with gross rent)<br><br>
🔮 <b>5-YEAR PROJECTION</b><br>====================<br>
Property Value Growth: €{total_appreciation:,.0f}<br>
Cumulative Cash Flow: €{total_cash_flow_5yr:,.0f}<br>
Total Return on Investment: {total_return_5yr:.1f}%<br><br>
💡 <b>DUTCH LANDLORD INSIGHTS:</b><br>===========================<br>
• Your monthly cash flow is {'positive' if net_monthly_cash_flow > 0 else 'negative'}<br>
• This investment provides a {'good' if cash_on_cash_return > 6 else 'moderate' if cash_on_cash_return > 4 else 'low'} return<br>
• The property will pay for itself in {gross_rent_multiplier:.1f} years of gross rent<br>
• After 5 years, you'll have earned €{total_cash_flow_5yr:,.0f} in cash flow plus €{total_appreciation:,.0f} in appreciation<br>"""
            # Cash Flow Chart (5 years, fixed y-axis)
            cash_flows = [annual_cash_flow * (i+1) for i in range(years)]
            cash_flow_fig = go.Figure()
            cash_flow_fig.add_trace(go.Bar(x=[f'Year {i+1}' for i in range(years)], y=cash_flows, name='Cumulative Cash Flow', marker_color='#3498db'))
            cash_flow_fig.update_layout(title='Cumulative Cash Flow Over 5 Years', xaxis_title='Year', yaxis_title='Cumulative Cash Flow (€)', plot_bgcolor='white', yaxis=dict(fixedrange=True, autorange=False))
            # ROI Chart (5 years, fixed y-axis)
            property_values = [total_purchase_price * ((1 + appreciation_rate/100)**(i+1)) for i in range(years)]
            roi = [((property_values[i] - total_purchase_price) + cash_flows[i]) / down_payment * 100 if down_payment else 0 for i in range(years)]
            roi_fig = go.Figure()
            roi_fig.add_trace(go.Scatter(x=[f'Year {i+1}' for i in range(years)], y=roi, mode='lines+markers', name='ROI', line=dict(color='#27ae60', width=3)))
            roi_fig.update_layout(title='Return on Investment Over 5 Years', xaxis_title='Year', yaxis_title='ROI (%)', plot_bgcolor='white', yaxis=dict(fixedrange=True, autorange=False))
            # Prepare new history entry
            entry = {
                'label': f"{units}u, €{purchase_price}/u, {down_payment_pct}% down, {mortgage_rate}% rate, {loan_term}y",  # Short summary
                'results': results,
                'cash_flow_fig': cash_flow_fig.to_dict(),
                'roi_fig': roi_fig.to_dict()
            }
            history.append(entry)
            options = [{'label': e['label'], 'value': i} for i, e in enumerate(history)]
            selected_idx = len(history) - 1
            # Build combined cash flow and ROI figures including all history entries
            combined_cash_fig = go.Figure()
            combined_roi_fig = go.Figure()
            for idx, h in enumerate(history):
                h_cash = h['cash_flow_fig']['data'][0]['y'] if h['cash_flow_fig']['data'] else []
                h_roi = h['roi_fig']['data'][0]['y'] if h['roi_fig']['data'] else []
                years_x = [f'Year {i+1}' for i in range(len(h_cash))]
                line_width = 4 if idx == selected_idx else 2
                opacity_val = 1.0 if idx == selected_idx else 0.4
                combined_cash_fig.add_trace(go.Scatter(x=years_x, y=h_cash, mode='lines+markers', name=h['label'], line=dict(width=line_width), opacity=opacity_val))
                combined_roi_fig.add_trace(go.Scatter(x=years_x, y=h_roi, mode='lines+markers', name=h['label'], line=dict(width=line_width), opacity=opacity_val))
            combined_cash_fig.update_layout(title='Cumulative Cash Flow Comparison', xaxis_title='Year', yaxis_title='Cumulative Cash Flow (€)', plot_bgcolor='white')
            combined_roi_fig.update_layout(title='ROI Comparison', xaxis_title='Year', yaxis_title='ROI (%)', plot_bgcolor='white')
            return dcc.Markdown(results, dangerously_allow_html=True), combined_cash_fig, combined_roi_fig, options, selected_idx, history
        # If dropdown changed, show selected
        elif triggered.startswith('landlord-history-dropdown'):
            if selected_idx is not None and selected_idx < len(history):
                entry = history[selected_idx]
                options = [{'label': e['label'], 'value': i} for i, e in enumerate(history)]
                return dcc.Markdown(entry['results'], dangerously_allow_html=True), entry['cash_flow_fig'], entry['roi_fig'], options, selected_idx, history
        # Default: show latest
        if history:
            entry = history[-1]
            options = [{'label': e['label'], 'value': i} for i, e in enumerate(history)]
            return dcc.Markdown(entry['results'], dangerously_allow_html=True), entry['cash_flow_fig'], entry['roi_fig'], options, len(history)-1, history
        return '', {}, {}, [], None, history 