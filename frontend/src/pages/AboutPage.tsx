import React from 'react';

function AboutPage() {
  return (
    <div style={{ backgroundColor: '#f5f6fa', minHeight: '100vh', padding: '20px' }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '20px',
        lineHeight: '1.6',
        fontSize: '16px',
        backgroundColor: 'white',
        boxShadow: '0 0 10px rgba(0,0,0,0.1)',
        borderRadius: '10px'
      }}>
        <h1 style={{ marginBottom: '30px' }}>About the Housing Market Simulation Model</h1>

        {/* How the Model Works Section */}
        <div>
          <h2 style={{ marginBottom: '20px', color: '#2c3e50' }}>How the Model Works</h2>
          
          {/* Visual representation of key components */}
          <div style={{ textAlign: 'center', marginBottom: '30px' }}>
            {/* Owner-Occupied */}
            <div style={{ display: 'inline-block', margin: '10px' }}>
              <div style={{
                width: '100px',
                height: '100px',
                backgroundColor: 'royalblue',
                margin: '10px',
                position: 'relative',
                display: 'inline-block'
              }}>
                <div style={{
                  width: '0',
                  height: '0',
                  borderLeft: '50px solid transparent',
                  borderRight: '50px solid transparent',
                  borderBottom: '40px solid #d95f02',
                  position: 'absolute',
                  top: '-40px',
                  left: '0'
                }} />
              </div>
              <p style={{ textAlign: 'center' }}>Owner-Occupied</p>
            </div>

            {/* Rented */}
            <div style={{ display: 'inline-block', margin: '10px' }}>
              <div style={{
                width: '100px',
                height: '100px',
                backgroundColor: 'limegreen',
                margin: '10px',
                position: 'relative',
                display: 'inline-block'
              }}>
                <div style={{
                  width: '0',
                  height: '0',
                  borderLeft: '50px solid transparent',
                  borderRight: '50px solid transparent',
                  borderBottom: '40px solid #d95f02',
                  position: 'absolute',
                  top: '-40px',
                  left: '0'
                }} />
              </div>
              <p style={{ textAlign: 'center' }}>Rented</p>
            </div>

            {/* Vacant */}
            <div style={{ display: 'inline-block', margin: '10px' }}>
              <div style={{
                width: '100px',
                height: '100px',
                backgroundColor: 'lightgray',
                margin: '10px',
                position: 'relative',
                display: 'inline-block'
              }}>
                <div style={{
                  width: '0',
                  height: '0',
                  borderLeft: '50px solid transparent',
                  borderRight: '50px solid transparent',
                  borderBottom: '40px solid #d95f02',
                  position: 'absolute',
                  top: '-40px',
                  left: '0'
                }} />
              </div>
              <p style={{ textAlign: 'center' }}>Vacant</p>
            </div>
          </div>

          <h3 style={{ marginBottom: '15px', color: '#2c3e50' }}>Key Components:</h3>
          <ul style={{ marginBottom: '30px' }}>
            <li>Housing Units: Each square represents a housing unit that can be either owner-occupied (blue), rented (green), or vacant (gray)</li>
            <li>Households: Represented by stick figures - owners (blue), renters (green), and unhoused (red)</li>
            <li>Monthly Simulation: The model advances month by month, simulating various market interactions</li>
          </ul>
        </div>

        {/* Tenant Search Process Section */}
        <div>
          <h2 style={{ marginBottom: '20px', color: '#2c3e50' }}>Tenant Search Process</h2>
          <p>
            The tenant search process occurs simultaneously for all households at each time step. Here's how it works:
            <ul>
              <li>All households evaluate their current situation at the same time</li>
              <li>Each household calculates their satisfaction score based on multiple factors</li>
              <li>Households then search for new housing in parallel, with the following priority:
                <ul>
                  <li>Unhoused households get first priority in unit selection</li>
                  <li>Households with lower satisfaction scores get higher priority</li>
                  <li>When multiple households want the same unit, the one with the best matching criteria (income, size, preferences) gets priority</li>
                </ul>
              </li>
            </ul>
          </p>
        </div>

        {/* Tenant Movement Motivations Section */}
        <div>
          <h2 style={{ marginBottom: '20px', color: '#2c3e50' }}>What Motivates Tenants to Move?</h2>
          <div style={{ display: 'flex', justifyContent: 'space-around', marginBottom: '30px' }}>
            <div style={{
              border: '2px solid #3498db',
              borderRadius: '10px',
              padding: '15px',
              margin: '10px',
              backgroundColor: '#f8f9fa'
            }}>
              <h4 style={{ color: '#3498db' }}>Financial Factors</h4>
              <ul>
                <li>High rent burden ({'>'}50% of income)</li>
                <li>Significant rent increases</li>
                <li>Better affordability elsewhere</li>
              </ul>
            </div>

            <div style={{
              border: '2px solid #2ecc71',
              borderRadius: '10px',
              padding: '15px',
              margin: '10px',
              backgroundColor: '#f8f9fa'
            }}>
              <h4 style={{ color: '#2ecc71' }}>Quality of Life</h4>
              <ul>
                <li>Low housing quality</li>
                <li>Inadequate unit size for household</li>
                <li>Poor location score</li>
              </ul>
            </div>

            <div style={{
              border: '2px solid #e74c3c',
              borderRadius: '10px',
              padding: '15px',
              margin: '10px',
              backgroundColor: '#f8f9fa'
            }}>
              <h4 style={{ color: '#e74c3c' }}>Life Changes</h4>
              <ul>
                <li>Changes in household size</li>
                <li>Income changes</li>
                <li>Life stage transitions</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Landlord Pricing Motivations Section */}
        <div>
          <h2 style={{ marginBottom: '20px', color: '#2c3e50' }}>What Drives Landlord Pricing?</h2>
          <div style={{ display: 'flex', justifyContent: 'space-around', marginBottom: '30px' }}>
            <div style={{
              border: '2px solid #9b59b6',
              borderRadius: '10px',
              padding: '15px',
              margin: '10px',
              backgroundColor: '#f8f9fa'
            }}>
              <h4 style={{ color: '#9b59b6' }}>Market Conditions</h4>
              <ul>
                <li>Local vacancy rates</li>
                <li>Average market rents</li>
                <li>Seasonal demand changes</li>
              </ul>
            </div>

            <div style={{
              border: '2px solid #f1c40f',
              borderRadius: '10px',
              padding: '15px',
              margin: '10px',
              backgroundColor: '#f8f9fa'
            }}>
              <h4 style={{ color: '#f1c40f' }}>Property Factors</h4>
              <ul>
                <li>Unit quality and amenities</li>
                <li>Recent renovations</li>
                <li>Location desirability</li>
              </ul>
            </div>

            <div style={{
              border: '2px solid #e67e22',
              borderRadius: '10px',
              padding: '15px',
              margin: '10px',
              backgroundColor: '#f8f9fa'
            }}>
              <h4 style={{ color: '#e67e22' }}>Regulatory Environment</h4>
              <ul>
                <li>Rent control policies</li>
                <li>Property tax rates</li>
                <li>Inspection requirements</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Key Parameters Section */}
        <div>
          <h2 style={{ marginBottom: '20px', color: '#2c3e50' }}>Key Parameters</h2>
          <div>
            <h3 style={{ marginBottom: '15px', color: '#2c3e50' }}>Housing Unit Parameters:</h3>
            <ul style={{ marginBottom: '20px' }}>
              <li>Quality: Affects property value and tenant satisfaction</li>
              <li>Rent: Monthly payment for tenants</li>
              <li>Property Value: Current market value of the unit</li>
            </ul>

            <h3 style={{ marginBottom: '15px', color: '#2c3e50' }}>Household Parameters:</h3>
            <ul style={{ marginBottom: '20px' }}>
              <li>Income: Monthly household income</li>
              <li>Wealth: Accumulated savings and assets</li>
              <li>Size: Number of household members</li>
              <li>Life Stage: Affects housing preferences and decisions</li>
              <li>Satisfaction: Measure of contentment with current housing situation</li>
            </ul>

            <h3 style={{ marginBottom: '15px', color: '#2c3e50' }}>Market Parameters:</h3>
            <ul>
              <li>Rent Cap (in cap scenario): Maximum allowed rent increase</li>
              <li>Mortgage Rates: Affects monthly payments for buyers</li>
              <li>Market Demand: Overall housing demand in the area</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AboutPage; 