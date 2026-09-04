import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [stats, setStats] = useState(null);
  const [payments, setPayments] = useState([]);
  const [attempts, setAttempts] = useState([]);
  const [analytics, setAnalytics] = useState(null);

  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [selectedPayment, setSelectedPayment] = useState(null);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError("");

      const [
        statsResponse,
        recoveryResponse,
        attemptsResponse,
        analyticsResponse,
      ] = await Promise.all([
        fetch(`${API_URL}/api/recovery/stats`),
        fetch(`${API_URL}/api/recovery`),
        fetch(`${API_URL}/api/recovery/attempts`),
        fetch(`${API_URL}/api/recovery/analytics`),
      ]);

      if (
        !statsResponse.ok ||
        !recoveryResponse.ok ||
        !attemptsResponse.ok ||
        !analyticsResponse.ok
      ) {
        throw new Error("Failed to fetch dashboard data");
      }

      const statsData = await statsResponse.json();
      const recoveryData = await recoveryResponse.json();
      const attemptsData = await attemptsResponse.json();
      const analyticsData = await analyticsResponse.json();

      setStats(statsData);
      setPayments(recoveryData.payments || []);
      setAttempts(attemptsData.attempts || []);
      setAnalytics(analyticsData);

      setSelectedPayment((current) => {
        if (!current) return null;
        return (recoveryData.payments || []).find(
          (payment) => payment.payment_id === current.payment_id
        ) || null;
      });
    } catch (err) {
      console.error(err);

      setError(
        "Unable to connect to the RecoveryAI backend. Make sure FastAPI is running."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const formatAmount = (amount, currency = "USD") => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
    }).format(amount);
  };

  const getLatestAttempt = (paymentId) => {
    const paymentAttempts = attempts
      .filter((attempt) => attempt.payment_id === paymentId)
      .sort((a, b) => b.attempt_id - a.attempt_id);

    return paymentAttempts[0] || null;
  };

  const getAttemptCount = (paymentId) => {
    return attempts.filter(
      (attempt) => attempt.payment_id === paymentId
    ).length;
  };

  const openPaymentDetails = (payment) => {
    setSelectedPayment(payment);
  };

  const closePaymentDetails = () => {
    setSelectedPayment(null);
  };

  const getPaymentAttempts = (paymentId) => {
    return attempts
      .filter((attempt) => attempt.payment_id === paymentId)
      .sort((a, b) => b.attempt_id - a.attempt_id);
  };

  const getActionExplanation = (payment) => {
    if (!payment?.recovery) return "No recovery recommendation available.";

    if (payment.recovery.action === "manual_review") {
      return `Automatic recovery has reached the retry threshold. ${payment.recovery.message}`;
    }

    if (payment.recovery.action === "retry_payment") {
      return `${payment.recovery.message} The system will stop automatic retries once the retry limit is reached.`;
    }

    return payment.recovery.message;
  };

  useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === "Escape") {
        closePaymentDetails();
      }
    };

    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, []);

  const createAttempt = async (paymentId) => {
    try {
      setActionLoading(`create-${paymentId}`);
      setError("");
      setSuccess("");

      const response = await fetch(
        `${API_URL}/api/recovery/attempts/${paymentId}`,
        {
          method: "POST",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Failed to create recovery attempt"
        );
      }

      setSuccess(
        `Recovery attempt #${data.attempt.id} created for payment #${paymentId}.`
      );

      await fetchDashboardData();
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setActionLoading(null);
    }
  };

  const executeAttempt = async (attemptId) => {
    try {
      setActionLoading(`execute-${attemptId}`);
      setError("");
      setSuccess("");

      const response = await fetch(
        `${API_URL}/api/recovery/attempts/${attemptId}/execute`,
        {
          method: "POST",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Failed to execute recovery attempt"
        );
      }

      if (data.execution?.success) {
        setSuccess(
          `Attempt #${attemptId}: ${data.execution.message}`
        );
      } else {
        setError(
          `Attempt #${attemptId}: ${
            data.execution?.message ||
            "Recovery attempt blocked."
          }`
        );
      }

      await fetchDashboardData();
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="app">
        <div className="loading-screen">
          <div className="spinner"></div>
          <h2>Loading RecoveryAI...</h2>
          <p>Connecting to the recovery engine</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">R</div>

          <div>
            <h1>RecoveryAI</h1>
            <span>Revenue Recovery Platform</span>
          </div>
        </div>

        <button
          className="refresh-button"
          onClick={fetchDashboardData}
          disabled={loading}
        >
          ↻ Refresh
        </button>
      </header>

      <main className="dashboard">
        <section className="page-heading">
          <div>
            <p className="eyebrow">OPERATIONS</p>

            <h2>Recovery Dashboard</h2>

            <p className="subtitle">
              Monitor failed payments and execute intelligent
              recovery strategies.
            </p>
          </div>
        </section>

        {error && (
          <div className="error-banner">
            {error}
          </div>
        )}

        {success && (
          <div className="success-banner">
            {success}
          </div>
        )}

        {stats && (
          <section className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon">!</div>

              <div>
                <p>Failed Payments</p>
                <h3>{stats.failed_payments}</h3>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">$</div>

              <div>
                <p>Failed Amount</p>

                <h3>
                  {formatAmount(
                    stats.total_failed_amount,
                    stats.currency
                  )}
                </h3>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">✓</div>

              <div>
                <p>Payment Success Rate</p>
                <h3>{stats.recovery_rate}%</h3>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">◉</div>

              <div>
                <p>Affected Customers</p>
                <h3>{stats.affected_customers}</h3>
              </div>
            </div>
          </section>
        )}

        {analytics && (
          <section className="analytics-section">
            <div className="section-header">
              <div>
                <p className="eyebrow">ANALYTICS</p>

                <h3>Recovery Performance</h3>

                <p>
                  Overview of recovery attempts processed by
                  the system.
                </p>
              </div>
            </div>

            <div className="analytics-grid">
              <div className="analytics-card">
                <span>Total Attempts</span>
                <strong>{analytics.total_attempts}</strong>
              </div>

              <div className="analytics-card">
                <span>Successful</span>
                <strong>
                  {analytics.successful_attempts}
                </strong>
              </div>

              <div className="analytics-card">
                <span>Failed</span>
                <strong>
                  {analytics.failed_attempts}
                </strong>
              </div>

              <div className="analytics-card">
                <span>Pending</span>
                <strong>
                  {analytics.pending_attempts}
                </strong>
              </div>

              <div className="analytics-card">
                <span>Recovery Attempt Success Rate</span>
                <strong>
                  {analytics.success_rate}%
                </strong>
              </div>
            </div>
          </section>
        )}

        {stats && (
          <section className="priority-section">
            <div className="section-header">
              <div>
                <p className="eyebrow">PRIORITY</p>

                <h3>Recovery Priority</h3>
              </div>
            </div>

            <div className="priority-grid">
              <div className="priority-card high">
                <span className="priority-label">
                  HIGH
                </span>

                <strong>
                  {stats.priority.high}
                </strong>

                <span>payments</span>
              </div>

              <div className="priority-card medium">
                <span className="priority-label">
                  MEDIUM
                </span>

                <strong>
                  {stats.priority.medium}
                </strong>

                <span>payments</span>
              </div>

              <div className="priority-card low">
                <span className="priority-label">
                  LOW
                </span>

                <strong>
                  {stats.priority.low}
                </strong>

                <span>payments</span>
              </div>
            </div>
          </section>
        )}

        <section className="queue-section">
          <div className="section-header">
            <div>
              <p className="eyebrow">
                RECOVERY QUEUE
              </p>

              <h3>Failed Payments</h3>

              <p>
                Payments requiring recovery action based on
                failure reason.
              </p>
            </div>

            <div className="queue-count">
              {payments.length} payments
            </div>
          </div>

          {payments.length === 0 ? (
            <div className="empty-state">
              <div>✓</div>

              <h3>No failed payments</h3>

              <p>
                Your recovery queue is currently clear.
              </p>
            </div>
          ) : (
            <div className="table-wrapper">
              <table className="recovery-table">
                <thead>
                  <tr>
                    <th>Customer</th>
                    <th>Payment</th>
                    <th>Amount</th>
                    <th>Failure Reason</th>
                    <th>Priority</th>
                    <th>Recommended Action</th>
                    <th>Recovery</th>
                  </tr>
                </thead>

                <tbody>
                  {payments.map((payment) => {
                    const latestAttempt =
                      getLatestAttempt(
                        payment.payment_id
                      );

                    const attemptCount =
                      getAttemptCount(
                        payment.payment_id
                      );

                    const isCreating =
                      actionLoading ===
                      `create-${payment.payment_id}`;

                    const isExecuting =
                      latestAttempt &&
                      actionLoading ===
                        `execute-${latestAttempt.attempt_id}`;

                    const isRetryStrategy =
                      payment.recovery.action === "retry_payment";

                    const retryLimitReached =
                      isRetryStrategy && attemptCount >= 3;

                    return (
                      <tr
                        key={payment.payment_id}
                        className="recovery-row"
                        onClick={() => openPaymentDetails(payment)}
                        tabIndex={0}
                        onKeyDown={(event) => {
                          if (event.key === "Enter" || event.key === " ") {
                            event.preventDefault();
                            openPaymentDetails(payment);
                          }
                        }}
                        aria-label={`View payment ${payment.payment_id} details`}
                      >
                        <td>
                          <div className="customer-cell">
                            <div className="avatar">
                              {payment.customer.name.charAt(
                                0
                              )}
                            </div>

                            <div>
                              <strong>
                                {payment.customer.name}
                              </strong>

                              <span>
                                {payment.customer.email}
                              </span>
                            </div>
                          </div>
                        </td>

                        <td>
                          <span className="payment-id">
                            #{payment.payment_id}
                          </span>
                        </td>

                        <td>
                          <strong>
                            {formatAmount(
                              payment.amount,
                              payment.currency
                            )}
                          </strong>
                        </td>

                        <td>
                          <span className="failure-reason">
                            {payment.failure_reason.replaceAll(
                              "_",
                              " "
                            )}
                          </span>
                        </td>

                        <td>
                          <span
                            className={`priority-badge ${payment.recovery.priority}`}
                          >
                            {payment.recovery.priority}
                          </span>
                        </td>

                        <td>
                          <div className="action-cell">
                            <strong>
                              {payment.recovery.action.replaceAll(
                                "_",
                                " "
                              )}
                            </strong>

                            <span>
                              {payment.recovery.message}
                            </span>
                          </div>
                        </td>

                        <td>
                          <div className="recovery-actions">
                            {!latestAttempt ? (
                              <button
                                className="action-button primary"
                                onClick={(event) => {
                                  event.stopPropagation();
                                  createAttempt(payment.payment_id);
                                }}
                                disabled={isCreating}
                              >
                                {isCreating
                                  ? "Creating..."
                                  : "Create Attempt"}
                              </button>
                            ) : latestAttempt.status ===
                                "pending" ? (
                              <div>
                                <div className="attempt-info">
                                  <span>
                                    Attempt #
                                    {
                                      latestAttempt.attempt_id
                                    }
                                  </span>

                                  <span
                                    className={`status-badge ${latestAttempt.status}`}
                                  >
                                    {latestAttempt.status}
                                  </span>
                                </div>

                                <button
                                  className="action-button primary"
                                  onClick={(event) => {
                                    event.stopPropagation();
                                    executeAttempt(latestAttempt.attempt_id);
                                  }}
                                  disabled={isExecuting}
                                >
                                  {isExecuting
                                    ? "Executing..."
                                    : "Execute"}
                                </button>
                              </div>
                            ) : latestAttempt.status ===
                                "sent" &&
                              isRetryStrategy &&
                              !retryLimitReached ? (
                              <div>
                                <div className="attempt-info">
                                  <span>
                                    Attempt #
                                    {
                                      latestAttempt.attempt_id
                                    }
                                  </span>

                                  <span
                                    className={`status-badge ${latestAttempt.status}`}
                                  >
                                    {latestAttempt.status}
                                  </span>
                                </div>

                                <button
                                  className="action-button primary"
                                  onClick={() =>
                                    createAttempt(
                                      payment.payment_id
                                    )
                                  }
                                  disabled={isCreating}
                                >
                                  {isCreating
                                    ? "Creating..."
                                    : "Create Next Attempt"}
                                </button>
                              </div>
                            ) : latestAttempt.status ===
                                "sent" &&
                              isRetryStrategy &&
                              retryLimitReached ? (
                              <div className="recovery-complete">
                                <div className="attempt-info">
                                  <span>
                                    Attempt #
                                    {
                                      latestAttempt.attempt_id
                                    }
                                  </span>

                                  <span className="status-badge sent">
                                    sent
                                  </span>
                                </div>

                                <span className="blocked-text">
                                  ✓ Retry Limit Reached
                                </span>
                              </div>
                            ) : latestAttempt.status ===
                                "sent" ? (
                              <div className="recovery-complete">
                                <div className="attempt-info">
                                  <span>
                                    Attempt #{
                                      latestAttempt.attempt_id
                                    }
                                  </span>

                                  <span className="status-badge sent">
                                    sent
                                  </span>
                                </div>

                                <span className="blocked-text">
                                  ✓ Recovery action completed
                                </span>
                              </div>
                            ) : latestAttempt.status ===
                                "failed" ? (
                              <div className="recovery-complete">
                                <div className="attempt-info">
                                  <span>
                                    Attempt #
                                    {
                                      latestAttempt.attempt_id
                                    }
                                  </span>

                                  <span className="status-badge failed">
                                    failed
                                  </span>
                                </div>

                                <span className="blocked-text">
                                  ⚠  Manual Review
                                </span>
                              </div>
                            ) : (
                              <div className="recovery-complete">
                                <div className="attempt-info">
                                  <span>
                                    Attempt #
                                    {
                                      latestAttempt.attempt_id
                                    }
                                  </span>

                                  <span
                                    className={`status-badge ${latestAttempt.status}`}
                                  >
                                    {latestAttempt.status}
                                  </span>
                                </div>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="attempts-section">
          <div className="section-header">
            <div>
              <p className="eyebrow">ACTIVITY</p>

              <h3>Recovery Attempts</h3>

              <p>
                Recent recovery actions processed by the
                system.
              </p>
            </div>

            <div className="queue-count">
              {attempts.length} attempts
            </div>
          </div>

          <div className="attempts-list">
            {attempts.length === 0 ? (
              <div className="empty-attempts">
                <strong>No recovery activity yet</strong>
                <span>
                  Actions taken by your recovery workflows will appear here.
                </span>
              </div>
            ) : (
              <div className="activity-timeline">
                {attempts
                  .slice()
                  .sort((a, b) => b.attempt_id - a.attempt_id)
                  .map((attempt, index) => {
                    const strategyLabel = attempt.strategy
                      .replaceAll("_", " ")
                      .replace(/\w/g, (char) => char.toUpperCase());

                    const statusLabel =
                      attempt.status.charAt(0).toUpperCase() +
                      attempt.status.slice(1);

                    const statusIcon =
                      attempt.status === "sent"
                        ? "✓"
                        : attempt.status === "failed"
                        ? "!"
                        : "•";

                    return (
                      <div
                        className={`activity-event activity-event-${attempt.status}`}
                        key={attempt.attempt_id}
                      >
                        <div className="activity-event-marker" aria-hidden="true">
                          {statusIcon}
                        </div>

                        {index < attempts.length - 1 && (
                          <div
                            className="activity-event-line"
                            aria-hidden="true"
                          />
                        )}

                        <div className="activity-event-content">
                          <div className="activity-event-top">
                            <div>
                              <span className="activity-event-title">
                                Recovery attempt #{attempt.attempt_id}
                              </span>
                              <span className="activity-event-meta">
                                Payment #{attempt.payment_id} ·{" "}
                                {attempt.customer?.name || "Unknown customer"}
                              </span>
                            </div>

                            <span
                              className={`status-badge ${attempt.status}`}
                            >
                              {statusLabel}
                            </span>
                          </div>

                          <div className="activity-event-details">
                            <span className="activity-event-strategy">
                              {strategyLabel}
                            </span>

                            <span className="activity-event-channel">
                              Channel: {attempt.channel || "system"}
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
              </div>
            )}
          </div>
        </section>

        {selectedPayment && (
          <>
            <button
              className="drawer-backdrop"
              aria-label="Close payment details"
              onClick={closePaymentDetails}
            />

            <aside
              className="payment-drawer"
              aria-label="Payment details"
            >
              <div className="drawer-header">
                <div>
                  <p className="eyebrow">PAYMENT DETAILS</p>
                  <h3>Payment #{selectedPayment.payment_id}</h3>
                </div>

                <button
                  className="drawer-close"
                  onClick={closePaymentDetails}
                  aria-label="Close payment details"
                >
                  ×
                </button>
              </div>

              <div className="drawer-customer">
                <div className="drawer-avatar">
                  {selectedPayment.customer.name.charAt(0)}
                </div>
                <div>
                  <strong>{selectedPayment.customer.name}</strong>
                  <span>{selectedPayment.customer.email}</span>
                </div>
              </div>

              <div className="drawer-summary">
                <div>
                  <span>Amount</span>
                  <strong>
                    {formatAmount(
                      selectedPayment.amount,
                      selectedPayment.currency
                    )}
                  </strong>
                </div>
                <div>
                  <span>Failure reason</span>
                  <strong>
                    {selectedPayment.failure_reason.replaceAll("_", " ")}
                  </strong>
                </div>
                <div>
                  <span>Priority</span>
                  <span
                    className={`priority-badge ${selectedPayment.recovery.priority}`}
                  >
                    {selectedPayment.recovery.priority}
                  </span>
                </div>
              </div>

              <div className="drawer-section">
                <p className="drawer-label">RECOMMENDED ACTION</p>
                <div className="drawer-action">
                  <strong>
                    {selectedPayment.recovery.action.replaceAll("_", " ")}
                  </strong>
                  <span>{selectedPayment.recovery.message}</span>
                </div>
              </div>

              <div className="drawer-section explanation-section">
                <p className="drawer-label">WHY THIS ACTION?</p>
                <p className="drawer-explanation">
                  {getActionExplanation(selectedPayment)}
                </p>
              </div>

              <div className="drawer-section">
                <div className="drawer-section-heading">
                  <p className="drawer-label">RECOVERY HISTORY</p>
                  <span>
                    {getAttemptCount(selectedPayment.payment_id)} attempts
                  </span>
                </div>

                <div className="recovery-history">
                  {getPaymentAttempts(selectedPayment.payment_id).length === 0 ? (
                    <div className="history-empty">
                      No recovery attempts yet.
                    </div>
                  ) : (
                    getPaymentAttempts(selectedPayment.payment_id).map(
                      (attempt) => (
                        <div
                          className="history-item"
                          key={attempt.attempt_id}
                        >
                          <div className="history-marker" />
                          <div className="history-content">
                            <div className="history-topline">
                              <strong>Attempt #{attempt.attempt_id}</strong>
                              <span
                                className={`status-badge ${attempt.status}`}
                              >
                                {attempt.status}
                              </span>
                            </div>
                            <span>
                              {attempt.strategy.replaceAll("_", " ")}
                            </span>
                          </div>
                        </div>
                      )
                    )
                  )}
                </div>
              </div>
            </aside>
          </>
        )}
      </main>
    </div>
  );
}

export default App;
