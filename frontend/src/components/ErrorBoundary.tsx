import React, { ReactNode, ReactElement } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error): void {
    console.error('Error caught by boundary:', error);
  }

  render(): ReactElement {
    if (this.state.hasError) {
      return (
        <div className="w-full min-h-screen flex items-center justify-center bg-surface px-4">
          <div className="text-center max-w-md card-surface p-8">
            <h1 className="font-display text-headline-md text-on-surface mb-2">Something went wrong</h1>
            <p className="text-body-sm text-on-surface-variant mb-6">
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="btn-primary mx-auto"
            >
              Reload Application
            </button>
          </div>
        </div>
      );
    }

    return this.props.children as ReactElement;
  }
}
