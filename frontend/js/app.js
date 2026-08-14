/**
 * CloudSage Frontend Dashboard Controller
 * Handles backend health checks, AWS STS connectivity, operational tools, and AI Assistant interactions.
 */

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements - Status Badges
  const backendStatusBadge = document.getElementById('backend-status-badge');
  const backendStatusText = document.getElementById('backend-status-text');
  const awsStatusBadge = document.getElementById('aws-status-badge');
  const awsStatusText = document.getElementById('aws-status-text');
  const awsConnectionMsg = document.getElementById('aws-connection-message');
  const awsValStatus = document.getElementById('aws-val-status');
  const awsValRegion = document.getElementById('aws-val-region');
  const awsValAccount = document.getElementById('aws-val-account');

  // DOM Elements - Results Viewer
  const resultsTitle = document.getElementById('results-title');
  const resultsBadge = document.getElementById('results-badge');
  const resultsStatusDot = document.getElementById('results-status-dot');
  const resultsViewRendered = document.getElementById('results-view-rendered');
  const resultsViewRaw = document.getElementById('results-view-raw');
  const emptyState = document.getElementById('empty-state');
  const renderedDataContainer = document.getElementById('rendered-data-container');
  const resultsRawJson = document.getElementById('results-raw-json');

  // DOM Elements - View Toggles
  const btnViewTable = document.getElementById('btn-view-table');
  const btnViewJson = document.getElementById('btn-view-json');

  // DOM Elements - Action Buttons & Inputs
  const btnRefreshAws = document.getElementById('btn-refresh-aws');
  const btnFetchEc2 = document.getElementById('btn-fetch-ec2');
  const btnFetchS3 = document.getElementById('btn-fetch-s3');
  const btnFetchCw = document.getElementById('btn-fetch-cw');
  const btnFetchCost = document.getElementById('btn-fetch-cost');

  const cwInstanceIdInput = document.getElementById('cw-instance-id');
  const cwHoursSelect = document.getElementById('cw-hours');
  const costDaysSelect = document.getElementById('cost-days');

  // Currency & Rate Configuration (Configurable development rate)
  const USD_TO_INR_RATE = 85.0;

  function formatInrCurrency(amount) {
    if (amount === null || amount === undefined || isNaN(amount)) return '₹0.00';
    const num = Math.abs(Number(amount));
    const parts = num.toFixed(2).split('.');
    let intPart = parts[0];
    const decPart = parts[1];
    
    if (intPart.length > 3) {
      const lastThree = intPart.substring(intPart.length - 3);
      let otherNumbers = intPart.substring(0, intPart.length - 3);
      const groups = [];
      while (otherNumbers.length > 2) {
        groups.unshift(otherNumbers.substring(otherNumbers.length - 2));
        otherNumbers = otherNumbers.substring(0, otherNumbers.length - 2);
      }
      if (otherNumbers.length > 0) groups.unshift(otherNumbers);
      intPart = groups.join(',') + ',' + lastThree;
    }
    const sign = amount < 0 ? '-' : '';
    return `${sign}₹${intPart}.${decPart}`;
  }

  let currentRawData = { status: "no query executed yet" };

  // ===========================================================================
  // 1. Backend Health Check
  // ===========================================================================
  async function checkBackendHealth() {
    try {
      const res = await fetch('/health', { headers: { 'Accept': 'application/json' } });
      const data = await res.json();
      if (res.ok && data.status === 'healthy') {
        backendStatusBadge.className = 'status-pill badge-healthy';
        backendStatusText.textContent = 'API Operational';
      } else {
        backendStatusBadge.className = 'status-pill badge-error';
        backendStatusText.textContent = 'API Degraded';
      }
    } catch (err) {
      backendStatusBadge.className = 'status-pill badge-error';
      backendStatusText.textContent = 'API Offline';
    }
  }

  // ===========================================================================
  // 2. AWS Connection Check (STS)
  // ===========================================================================
  async function checkAwsConnection() {
    try {
      awsStatusBadge.className = 'status-pill badge-pending';
      awsStatusText.textContent = 'Checking AWS...';
      if (awsValStatus) awsValStatus.textContent = 'Inspecting...';

      const res = await fetch('/api/aws/status', { headers: { 'Accept': 'application/json' } });
      const data = await res.json();

      if (res.ok && data.connected) {
        awsStatusBadge.className = 'status-pill badge-connected';
        awsStatusText.textContent = 'AWS Connected';
        if (awsValStatus) {
          awsValStatus.textContent = 'Connected (STS)';
          awsValStatus.className = 'telemetry-value text-accent';
        }
        if (awsValRegion) awsValRegion.textContent = data.region || 'us-east-1';
        if (awsValAccount) awsValAccount.textContent = data.account_id ? `...${data.account_id.slice(-4)}` : 'Authenticated';
        if (awsConnectionMsg) awsConnectionMsg.textContent = `Connected to AWS Region: ${data.region} as ${data.arn || 'IAM Principal'}.`;
      } else {
        awsStatusBadge.className = 'status-pill badge-disconnected';
        awsStatusText.textContent = 'AWS Not Connected';
        if (awsValStatus) {
          awsValStatus.textContent = 'Not Connected';
          awsValStatus.className = 'telemetry-value';
        }
        if (awsValRegion) awsValRegion.textContent = data.region || 'us-east-1';
        if (awsValAccount) awsValAccount.textContent = 'None';
        if (awsConnectionMsg) awsConnectionMsg.textContent = data.message || 'AWS credentials not configured. Running safely in Development Mock mode.';
      }
    } catch (err) {
      awsStatusBadge.className = 'status-pill badge-error';
      awsStatusText.textContent = 'Check Failed';
      if (awsValStatus) awsValStatus.textContent = 'Error';
      if (awsConnectionMsg) awsConnectionMsg.textContent = `Error connecting to backend AWS status endpoint: ${err.message}`;
    }
  }

  // ===========================================================================
  // 3. View Switcher Helpers
  // ===========================================================================
  function setResultsPayload(title, badgeText, data, isSuccess = true) {
    currentRawData = data;
    if (resultsTitle) resultsTitle.textContent = title;
    if (resultsBadge) resultsBadge.textContent = badgeText;
    if (resultsStatusDot) resultsStatusDot.className = isSuccess ? 'results-status-dot active' : 'results-status-dot';
    if (resultsRawJson) resultsRawJson.textContent = JSON.stringify(data, null, 2);

    if (emptyState) emptyState.classList.add('hidden');
    if (renderedDataContainer) renderedDataContainer.classList.remove('hidden');
  }

  if (btnViewTable) {
    btnViewTable.addEventListener('click', () => {
      btnViewTable.classList.add('active');
      if (btnViewJson) btnViewJson.classList.remove('active');
      if (resultsViewRendered) resultsViewRendered.classList.remove('hidden');
      if (resultsViewRaw) resultsViewRaw.classList.add('hidden');
    });
  }

  if (btnViewJson) {
    btnViewJson.addEventListener('click', () => {
      btnViewJson.classList.add('active');
      if (btnViewTable) btnViewTable.classList.remove('active');
      if (resultsViewRaw) resultsViewRaw.classList.remove('hidden');
      if (resultsViewRendered) resultsViewRendered.classList.add('hidden');
    });
  }

  // ===========================================================================
  // 4. EC2 Inspector Handler
  // ===========================================================================
  async function fetchEc2Instances() {
    setResultsPayload('EC2 Inspector', 'Fetching...', { status: 'loading' });
    renderedDataContainer.innerHTML = '<p class="text-secondary">Querying EC2 instances across region...</p>';

    try {
      const res = await fetch('/api/aws/ec2/instances');
      const data = await res.json();

      setResultsPayload('EC2 Instance Inventory', `${data.count || 0} Instances`, data, data.success);

      if (!data.success) {
        renderedDataContainer.innerHTML = `
          <div class="security-note" style="border-color: var(--danger-border); background: var(--danger-subtle);">
            <span><strong>AWS EC2 Error:</strong> ${data.error || 'Failed to list instances'}</span>
          </div>`;
        return;
      }

      if (data.count === 0) {
        renderedDataContainer.innerHTML = `
          <div class="empty-state">
            <p>No EC2 instances found in region <strong>${data.region}</strong>.</p>
          </div>`;
        return;
      }

      let rowsHtml = data.instances.map(inst => {
        const stateClass = inst.state === 'running' ? 'state-running' : (inst.state === 'stopped' ? 'state-stopped' : 'state-terminated');
        return `
          <tr>
            <td><span class="state-pill ${stateClass}">${inst.state}</span></td>
            <td><strong class="font-mono clickable-id" data-id="${inst.instance_id}" title="Click to test CloudWatch">${inst.instance_id}</strong></td>
            <td>${inst.name || '<span class="text-muted">None</span>'}</td>
            <td><span class="font-mono">${inst.instance_type || '--'}</span></td>
            <td><span class="text-muted font-mono">${inst.availability_zone || '--'}</span></td>
            <td><span class="font-mono">${inst.private_ip || '--'}</span></td>
            <td><span class="font-mono text-accent">${inst.public_ip || '--'}</span></td>
          </tr>
        `;
      }).join('');

      renderedDataContainer.innerHTML = `
        <div class="data-table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>State</th>
                <th>Instance ID</th>
                <th>Name Tag</th>
                <th>Type</th>
                <th>AZ</th>
                <th>Private IP</th>
                <th>Public IP</th>
              </tr>
            </thead>
            <tbody>${rowsHtml}</tbody>
          </table>
        </div>
      `;

      // Prefill CloudWatch instance ID on click
      document.querySelectorAll('.clickable-id').forEach(el => {
        el.addEventListener('click', (e) => {
          const instId = e.target.getAttribute('data-id');
          if (cwInstanceIdInput && instId) {
            cwInstanceIdInput.value = instId;
            cwInstanceIdInput.focus();
          }
        });
      });

    } catch (err) {
      setResultsPayload('EC2 Inspector', 'Error', { error: err.message }, false);
      renderedDataContainer.innerHTML = `<p class="text-rose">Network error: ${err.message}</p>`;
    }
  }

  // ===========================================================================
  // 5. S3 Explorer Handler
  // ===========================================================================
  async function fetchS3Buckets() {
    setResultsPayload('S3 Explorer', 'Fetching...', { status: 'loading' });
    renderedDataContainer.innerHTML = '<p class="text-secondary">Querying S3 buckets in account...</p>';

    try {
      const res = await fetch('/api/aws/s3/buckets');
      const data = await res.json();

      setResultsPayload('S3 Storage Explorer', `${data.count || 0} Buckets`, data, data.success);

      if (!data.success) {
        renderedDataContainer.innerHTML = `
          <div class="security-note" style="border-color: var(--danger-border); background: var(--danger-subtle);">
            <span><strong>AWS S3 Error:</strong> ${data.error || 'Failed to list buckets'}</span>
          </div>`;
        return;
      }

      if (data.count === 0) {
        renderedDataContainer.innerHTML = `
          <div class="empty-state">
            <p>No S3 buckets found in this AWS account.</p>
          </div>`;
        return;
      }

      let rowsHtml = data.buckets.map(b => `
        <tr>
          <td><strong class="font-mono">${b.name}</strong></td>
          <td><span class="text-muted font-mono">${b.creation_date ? new Date(b.creation_date).toLocaleDateString() : '--'}</span></td>
          <td><span class="state-pill state-running">Active</span></td>
        </tr>
      `).join('');

      renderedDataContainer.innerHTML = `
        <div class="data-table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Bucket Name</th>
                <th>Creation Date</th>
                <th>Access Status</th>
              </tr>
            </thead>
            <tbody>${rowsHtml}</tbody>
          </table>
        </div>
      `;

    } catch (err) {
      setResultsPayload('S3 Explorer', 'Error', { error: err.message }, false);
      renderedDataContainer.innerHTML = `<p class="text-rose">Network error: ${err.message}</p>`;
    }
  }

  // ===========================================================================
  // 6. CloudWatch Metrics Handler
  // ===========================================================================
  async function fetchCloudWatchMetrics() {
    const instanceId = (cwInstanceIdInput.value || '').trim() || 'i-03fa78bc91204d8ef';
    const hours = cwHoursSelect.value || 1;

    setResultsPayload('CloudWatch Telemetry', 'Querying...', { status: 'loading' });
    renderedDataContainer.innerHTML = `<p class="text-secondary">Querying CPU utilization for instance ${instanceId} (${hours}h window)...</p>`;

    try {
      const res = await fetch(`/api/aws/cloudwatch/ec2/${encodeURIComponent(instanceId)}/cpu?hours=${hours}`);
      const data = await res.json();

      setResultsPayload(`CloudWatch Telemetry: ${instanceId}`, `${data.datapoint_count || 0} Points`, data, data.success);

      if (!data.success) {
        renderedDataContainer.innerHTML = `
          <div class="security-note" style="border-color: var(--danger-border); background: var(--danger-subtle);">
            <span><strong>CloudWatch Error:</strong> ${data.error || 'Failed to retrieve metrics'}</span>
          </div>`;
        return;
      }

      const avgText = data.average_cpu !== null ? `${data.average_cpu}%` : '--';
      const maxText = data.max_cpu !== null ? `${data.max_cpu}%` : '--';
      const minText = data.min_cpu !== null ? `${data.min_cpu}%` : '--';

      let datapointsHtml = '';
      if (data.datapoints && data.datapoints.length > 0) {
        datapointsHtml = data.datapoints.map(dp => `
          <tr>
            <td class="font-mono text-muted">${new Date(dp.timestamp).toLocaleTimeString()}</td>
            <td><strong class="font-mono">${dp.average}%</strong></td>
            <td class="font-mono text-muted">${dp.maximum}%</td>
            <td class="font-mono text-muted">${dp.minimum}%</td>
          </tr>
        `).join('');
      } else {
        datapointsHtml = `<tr><td colspan="4" class="text-muted" style="text-align:center;">${data.message || 'No datapoints recorded.'}</td></tr>`;
      }

      renderedDataContainer.innerHTML = `
        <div class="metric-summary-banner">
          <div class="metric-summary-box">
            <span class="telemetry-label">Average CPU</span>
            <span class="telemetry-value text-accent">${avgText}</span>
          </div>
          <div class="metric-summary-box">
            <span class="telemetry-label">Peak CPU</span>
            <span class="telemetry-value">${maxText}</span>
          </div>
          <div class="metric-summary-box">
            <span class="telemetry-label">Min CPU</span>
            <span class="telemetry-value">${minText}</span>
          </div>
          <div class="metric-summary-box">
            <span class="telemetry-label">Datapoints</span>
            <span class="telemetry-value font-mono">${data.datapoint_count}</span>
          </div>
        </div>

        <div class="data-table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Average</th>
                <th>Maximum</th>
                <th>Minimum</th>
              </tr>
            </thead>
            <tbody>${datapointsHtml}</tbody>
          </table>
        </div>
      `;

    } catch (err) {
      setResultsPayload('CloudWatch Telemetry', 'Error', { error: err.message }, false);
      renderedDataContainer.innerHTML = `<p class="text-rose">Network error: ${err.message}</p>`;
    }
  }

  // ===========================================================================
  // 7. Cost Intelligence Handler (INR Formatted)
  // ===========================================================================
  async function fetchCostSummary() {
    const days = costDaysSelect.value || 30;
    setResultsPayload('Cost Intelligence', 'Calculating...', { status: 'loading' });
    renderedDataContainer.innerHTML = `<p class="text-secondary">Querying AWS Cost Explorer (${days} days lookback)...</p>`;

    try {
      const res = await fetch(`/api/aws/cost/summary?days=${days}`);
      const data = await res.json();

      const totalUsd = Number(data.total_cost || 0);
      const totalInr = data.currency === 'INR' ? totalUsd : totalUsd * USD_TO_INR_RATE;
      const totalFormatted = formatInrCurrency(totalInr);

      setResultsPayload('Cost Intelligence Summary', `${totalFormatted}`, data, data.success);

      if (!data.success) {
        renderedDataContainer.innerHTML = `
          <div class="security-note" style="border-color: var(--warning-border); background: var(--warning-subtle);">
            <span><strong>Cost Explorer Advisory:</strong> ${data.error || 'Cost Explorer unavailable'}</span>
          </div>`;
        return;
      }

      let breakdownHtml = '';
      if (data.services && data.services.length > 0) {
        breakdownHtml = data.services.map(svc => {
          const svcUsd = Number(svc.cost || 0);
          const svcInr = data.currency === 'INR' ? svcUsd : svcUsd * USD_TO_INR_RATE;
          const svcFormatted = formatInrCurrency(svcInr);
          return `
            <div class="cost-item">
              <div class="cost-row">
                <span class="cost-service-name">${svc.service}</span>
                <span class="cost-amount">${svcFormatted} (${svc.percentage}%)</span>
              </div>
              <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width: ${Math.min(100, Math.max(2, svc.percentage))}%;"></div>
              </div>
            </div>
          `;
        }).join('');
      } else {
        breakdownHtml = '<p class="text-muted">No service breakdown data recorded for this period.</p>';
      }

      renderedDataContainer.innerHTML = `
        <div class="metric-summary-banner">
          <div class="metric-summary-box">
            <span class="telemetry-label">Total Spend (INR)</span>
            <span class="telemetry-value text-accent">${totalFormatted}</span>
            <span class="text-muted" style="font-size:0.68rem; margin-top:2px;">Converted at ₹${USD_TO_INR_RATE.toFixed(2)}/USD</span>
          </div>
          <div class="metric-summary-box">
            <span class="telemetry-label">Top Cost Driver</span>
            <span class="telemetry-value" style="font-size:0.78rem;">${data.top_service || 'None'}</span>
          </div>
          <div class="metric-summary-box">
            <span class="telemetry-label">Billing Period</span>
            <span class="telemetry-value font-mono" style="font-size:0.75rem;">${data.start_date} → ${data.end_date}</span>
          </div>
        </div>

        <h4 style="font-size:0.82rem; font-weight:600; margin-bottom:0.5rem; color:var(--text-secondary);">Service Expenditure Breakdown</h4>
        <div class="cost-breakdown-list">${breakdownHtml}</div>
      `;

    } catch (err) {
      setResultsPayload('Cost Intelligence', 'Error', { error: err.message }, false);
      renderedDataContainer.innerHTML = `<p class="text-rose">Network error: ${err.message}</p>`;
    }
  }

  // DOM Elements - GenAI Chat Assistant
  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  const btnChatSend = document.getElementById('btn-chat-send');
  const chatStream = document.getElementById('chat-stream');
  const btnResetChat = document.getElementById('btn-reset-chat');
  const chipPrompts = document.querySelectorAll('.chip-prompt');

  let currentSessionId = localStorage.getItem('cloudsage_session_id') || null;

  // ===========================================================================
  // 8. GenAI Chat Assistant Logic
  // ===========================================================================

  function formatMarkdown(text) {
    if (!text) return '';
    let html = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/### (.*?)$/gm, '<h3>$1</h3>')
      .replace(/## (.*?)$/gm, '<h3 style="color:var(--primary);">$1</h3>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/^&gt; (.*?)$/gm, '<blockquote>$1</blockquote>');

    const lines = html.split('\n');
    let inList = false;
    const processedLines = [];

    for (let line of lines) {
      if (line.trim().startsWith('- ')) {
        if (!inList) {
          processedLines.push('<ul>');
          inList = true;
        }
        processedLines.push(`<li>${line.trim().substring(2)}</li>`);
      } else {
        if (inList) {
          processedLines.push('</ul>');
          inList = false;
        }
        if (line.trim().length > 0 && !line.startsWith('<h3') && !line.startsWith('<blockquote') && !line.startsWith('<ul')) {
          processedLines.push(`<p>${line}</p>`);
        } else {
          processedLines.push(line);
        }
      }
    }
    if (inList) processedLines.push('</ul>');

    return processedLines.join('\n');
  }

  function appendUserMessage(text) {
    if (!chatStream) return;
    const msgEl = document.createElement('div');
    msgEl.className = 'chat-message message-user';
    msgEl.innerHTML = `
      <div class="message-avatar">
        <div class="avatar-icon user-avatar">👤</div>
      </div>
      <div class="message-body">
        <div class="message-header">
          <span class="message-sender">You</span>
          <span class="message-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
        </div>
        <div class="message-content">
          <p>${text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</p>
        </div>
      </div>
    `;
    chatStream.appendChild(msgEl);
    chatStream.scrollTop = chatStream.scrollHeight;
  }

  function showThinkingBubble() {
    if (!chatStream) return null;
    const thinkingEl = document.createElement('div');
    thinkingEl.id = 'thinking-bubble-active';
    thinkingEl.className = 'chat-message message-ai';
    thinkingEl.innerHTML = `
      <div class="message-avatar">
        <div class="avatar-icon ai-avatar">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2a8 8 0 0 0-8 8c0 5 8 12 8 12s8-7 8-12a8 8 0 0 0-8-8z"/>
            <circle cx="12" cy="10" r="3"/>
          </svg>
        </div>
      </div>
      <div class="message-body" style="background: var(--surface-subtle); border-style: dashed;">
        <div class="thinking-bubble">
          <span>CloudSage reasoning & analyzing tools</span>
          <div class="thinking-dots">
            <span class="thinking-dot"></span>
            <span class="thinking-dot"></span>
            <span class="thinking-dot"></span>
          </div>
        </div>
      </div>
    `;
    chatStream.appendChild(thinkingEl);
    chatStream.scrollTop = chatStream.scrollHeight;
    return thinkingEl;
  }

  function appendAIMessage(answer, toolsUsed = [], dataSource = 'mock', sources = [], retrievalUsed = false) {
    if (!chatStream) return;

    const thinkingBubble = document.getElementById('thinking-bubble-active');
    if (thinkingBubble) thinkingBubble.remove();

    const msgEl = document.createElement('div');
    msgEl.className = 'chat-message message-ai';

    let metaPillsHtml = '';
    if (toolsUsed && toolsUsed.length > 0) {
      toolsUsed.forEach(tool => {
        metaPillsHtml += `<span class="tool-badge-pill">Tool · <strong>${tool}</strong></span>`;
      });
    }

    if (retrievalUsed || dataSource === 'knowledge_base') {
      metaPillsHtml += `<span class="source-badge-pill source-badge-rag">Knowledge Base</span>`;
    }

    if (dataSource === 'hybrid') {
      metaPillsHtml += `<span class="source-badge-pill source-badge-hybrid">Hybrid · AWS + RAG</span>`;
    } else if (dataSource === 'aws') {
      metaPillsHtml += `<span class="source-badge-pill source-badge-aws">Data · AWS Live</span>`;
    } else if (dataSource === 'mock') {
      metaPillsHtml += `<span class="source-badge-pill source-badge-mock">Development Mock</span>`;
    }

    const formattedContent = formatMarkdown(answer);

    let sourcesHtml = '';
    if (sources && sources.length > 0) {
      const sourceItems = sources.map(s => {
        const urlAttr = s.url ? `href="${s.url}" target="_blank" rel="noopener noreferrer"` : 'href="javascript:void(0)"';
        return `
          <li class="source-item">
            <a ${urlAttr} class="source-tag" title="${s.source || 'AWS Documentation'}">
              <span>• ${s.title}</span>
              <span style="opacity: 0.65; font-size: 0.68rem;">(${s.category || 'AWS'})</span>
            </a>
          </li>
        `;
      }).join('');

      sourcesHtml = `
        <div class="message-sources-box">
          <div class="sources-header">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
            </svg>
            <span>Documentation Sources</span>
          </div>
          <ul class="sources-list">${sourceItems}</ul>
        </div>
      `;
    }

    msgEl.innerHTML = `
      <div class="message-avatar">
        <div class="avatar-icon ai-avatar">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2a8 8 0 0 0-8 8c0 5 8 12 8 12s8-7 8-12a8 8 0 0 0-8-8z"/>
            <circle cx="12" cy="10" r="3"/>
          </svg>
        </div>
      </div>
      <div class="message-body">
        <div class="message-header">
          <span class="message-sender">CloudSage AI</span>
          <span class="message-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
        </div>
        <div class="message-content">
          ${formattedContent}
        </div>
        ${sourcesHtml}
        <div class="message-meta-bar">
          ${metaPillsHtml}
        </div>
      </div>
    `;

    chatStream.appendChild(msgEl);
    chatStream.scrollTop = chatStream.scrollHeight;
  }

  async function sendChatMessage(messageText) {
    const text = (messageText || '').trim();
    if (!text) return;

    if (chatInput) {
      chatInput.value = '';
      chatInput.disabled = true;
    }
    if (btnChatSend) btnChatSend.disabled = true;

    appendUserMessage(text);
    showThinkingBubble();

    try {
      const payload = {
        message: text,
        session_id: currentSessionId
      };

      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      const data = await res.json();

      if (res.ok) {
        if (data.session_id) {
          currentSessionId = data.session_id;
          localStorage.setItem('cloudsage_session_id', currentSessionId);
        }
        appendAIMessage(
          data.answer,
          data.tools_used,
          data.data_source,
          data.sources || [],
          data.retrieval_used || false
        );
      } else {
        appendAIMessage(
          `⚠️ **Assistant Error**: ${data.detail || 'Failed to process request.'}`,
          [],
          'system',
          [],
          false
        );
      }
    } catch (err) {
      appendAIMessage(
        `⚠️ **Network Error**: Could not connect to /api/chat (${err.message}). Is the FastAPI backend server running?`,
        [],
        'system',
        [],
        false
      );
    } finally {
      if (chatInput) {
        chatInput.disabled = false;
        chatInput.focus();
      }
      if (btnChatSend) btnChatSend.disabled = false;
    }
  }

  async function resetChatSession() {
    if (currentSessionId) {
      try {
        await fetch('/api/chat/reset', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: currentSessionId })
        });
      } catch (e) {
        console.warn('Session reset call failed:', e);
      }
    }

    currentSessionId = null;
    localStorage.removeItem('cloudsage_session_id');

    if (chatStream) {
      chatStream.innerHTML = `
        <div class="chat-message message-ai">
          <div class="message-avatar">
            <div class="avatar-icon ai-avatar">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 2a8 8 0 0 0-8 8c0 5 8 12 8 12s8-7 8-12a8 8 0 0 0-8-8z"/>
                <circle cx="12" cy="10" r="3"/>
              </svg>
            </div>
          </div>
          <div class="message-body">
            <div class="message-header">
              <span class="message-sender">CloudSage AI</span>
              <span class="message-time">New Session</span>
            </div>
            <div class="message-content">
              <p>Conversation memory reset. I am ready for new queries about your AWS infrastructure, resources, CPU telemetry, and cost breakdowns in <strong>₹ INR</strong>.</p>
            </div>
          </div>
        </div>
      `;
    }
  }

  // ===========================================================================
  // 9. Event Listeners Initialization
  // ===========================================================================
  if (btnRefreshAws) btnRefreshAws.addEventListener('click', checkAwsConnection);
  if (btnFetchEc2) btnFetchEc2.addEventListener('click', fetchEc2Instances);
  if (btnFetchS3) btnFetchS3.addEventListener('click', fetchS3Buckets);
  if (btnFetchCw) btnFetchCw.addEventListener('click', fetchCloudWatchMetrics);
  if (btnFetchCost) btnFetchCost.addEventListener('click', fetchCostSummary);

  if (chatForm) {
    chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const val = (chatInput ? chatInput.value : '').trim();
      if (val) sendChatMessage(val);
    });
  }

  if (btnResetChat) {
    btnResetChat.addEventListener('click', resetChatSession);
  }

  chipPrompts.forEach(chip => {
    chip.addEventListener('click', () => {
      const prompt = chip.getAttribute('data-prompt');
      if (prompt) {
        if (chatInput) chatInput.value = prompt;
        sendChatMessage(prompt);
      }
    });
  });

  // Initial checks
  checkBackendHealth();
  checkAwsConnection();
});
