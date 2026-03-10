import { useState, type FormEvent } from 'react';
import { useSettingsContext } from '../../app/useSettingsContext';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { InlineNotice } from '../../components/ui/InlineNotice';
import { TextField } from '../../components/ui/TextField';
import { validateEmail } from '../../lib/forms/validators';
import styles from './SettingsPage.module.css';
import { getThemeLabel } from './themeLabel';

export function SettingsPage(): JSX.Element {
  const { loading, saveSettings, settings } = useSettingsContext();
  const [inviteEmail, setInviteEmail] = useState('');
  const [formError, setFormError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  async function handleInviteSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();

    const error = validateEmail(inviteEmail);
    if (error) {
      setFormError(error);
      setSuccessMessage(null);
      return;
    }

    setFormError(null);
    setSuccessMessage(`Invite queued for ${inviteEmail.trim()}.`);
    setInviteEmail('');
  }

  return (
    <section className={styles.page}>
      <header className={styles.header}>
        <span className={styles.eyebrow}>Preferences and guardrails</span>
        <h2 className={styles.title}>Settings</h2>
        <p className={styles.copy}>Keep operating preferences aligned with the dashboard and invite admins without breaking validation rules.</p>
      </header>

      <div className={styles.stack}>
        <Card>
          <div className={styles.toggleRow}>
            <div className={styles.toggleCopy}>
              <p className={styles.toggleTitle}>Low-stock alerts</p>
              <p className={styles.toggleText}>Controls the alert rail shown on the dashboard.</p>
            </div>
            <label>
              <span className="sr-only">Low-stock alerts</span>
              <input
                aria-label="Low-stock alerts"
                checked={Boolean(settings?.lowStockAlerts)}
                onChange={(event) => {
                  void saveSettings({ lowStockAlerts: event.currentTarget.checked });
                }}
                type="checkbox"
              />
            </label>
          </div>
          {loading ? <InlineNotice>Saving preferences…</InlineNotice> : null}
        </Card>

        <Card>
          <p className={styles.toggleTitle}>Theme preference</p>
          <p className={styles.toggleText}>Theme preference: {getThemeLabel(settings?.theme ?? 'system')}</p>
        </Card>

        <Card>
          <form className={styles.form} onSubmit={(event) => void handleInviteSubmit(event)}>
            <TextField
              id="invite-email"
              label="Invite admin email"
              onChange={(event) => setInviteEmail(event.currentTarget.value)}
              placeholder="admin@northstarops.dev"
              type="email"
              value={inviteEmail}
            />
            <div>
              <Button type="submit">Send invite</Button>
            </div>
          </form>
          {formError ? <InlineNotice tone="error">{formError}</InlineNotice> : null}
          {successMessage ? <InlineNotice tone="success">{successMessage}</InlineNotice> : null}
        </Card>
      </div>
    </section>
  );
}
