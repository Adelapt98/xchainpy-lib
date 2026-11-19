# XChainPY roadmap

XChainPY is being developed as a maintainable multi-chain Python SDK. These are planned milestones, not features already available or promised delivery dates. Reliability of existing workflows comes before expanding the number of supported chains.

## 1. Trustworthy source and reproducible development

- Lock a supported Python and dependency matrix across active packages.
- Add CI for source installation, imports, dependency consistency and offline tests.
- Align package metadata and examples with current interfaces and supported networks.

**Completion:** a fresh checkout installs consistently, all active packages pass automated checks, and live credential material is absent from source and retained published history.

## 2. Dependable Bitcoin transactions

- Use integer base units and explicit decimal conversion at transaction boundaries.
- Cover fee estimation, change thresholds, multiple UTXOs, insufficient balances and signature failures.
- Define predictable coin selection and document treatment of unconfirmed outputs.
- Extend transaction-history pagination and explicit provider failure handling.

**Completion:** deterministic tests exercise normal spends and boundary cases without network access, alongside a reproducible opt-in disposable testnet workflow.

## 3. Consistent provider contracts

- Standardize timeout, rate-limit and provider-error handling.
- Make pagination, transaction status and asset units explicit across return values.
- Test malformed responses, partial failures and retries.
- Modernize Litecoin and Bitcoin Cash provider integrations with chain-specific fixtures.

**Completion:** applications can distinguish invalid input, unavailable providers and empty results, supported by common and adapter-specific contract tests.

## 4. Solana native-asset client

- Define SOL assets and configurable mainnet/devnet RPC settings.
- Implement address derivation and validation, balance reads, fees and transaction status.
- Add native SOL transaction construction, local signing and explicit submission.
- Test blockhash expiry, RPC failures, base-unit conversion and serialized transactions.

**Completion:** a separate adapter package passes offline contracts and includes an opt-in devnet verification guide using disposable keys. Token and program interactions are separate follow-on work.

## 5. Cosmos ecosystem and XRP Ledger clients

- Add a Cosmos SDK adapter for a clearly selected network, starting with native ATOM balance, address validation, fee estimation, transaction construction, signing and broadcast.
- Keep chain ID, denomination, RPC/REST endpoints and address-prefix settings configurable so the adapter can support other Cosmos SDK networks without assuming they are interchangeable.
- Add an XRP Ledger adapter for XRP account balances, sequence and fee handling, transaction construction, local signing, submission and validated-ledger status.
- Cover memo/tag handling, reserve requirements, network errors and base-unit precision with offline fixtures, then document opt-in testnet checks.

**Completion:** both adapters meet shared client contracts, pass deterministic offline tests, and document their network-specific transaction rules and testnet verification steps.

## 6. Ethereum and additional EVM workflows

- Validate nonce handling, chain IDs, gas estimates and EIP-1559 transaction fields.
- Extend native-asset and ERC-20 regression coverage and an opt-in Sepolia workflow.
- Separate endpoint configuration from credential storage and clarify HTTP/WebSocket support.
- Design reusable EVM configuration before adding Polygon, Arbitrum or BNB Smart Chain.
- Add Polygon and Arbitrum as separate network configurations after validating chain IDs, native token units, RPC behavior and finality assumptions. Add BNB Smart Chain only with its own provider and compatibility tests.

**Completion:** documented native and token workflows have deterministic fixtures, explicit failures and recorded integration results. Sharing the EVM alone does not establish support for another network.

## 7. Additional high-demand networks

- Evaluate Dogecoin as a UTXO-family adapter, with its own address, fee, dust and transaction serialization rules rather than reusing Bitcoin assumptions without validation.
- Add Cardano through a maintained provider interface, with explicit network selection, address validation, UTXO selection, fee calculation and transaction submission boundaries.
- Prioritize additional candidates such as Avalanche and Base only after reviewing developer demand, maintained public endpoints or libraries, licensing, and the effort required for reliable transaction support.
- For every new chain, define the supported scope first. Separate read-only support from transaction signing and broadcasting, and do not mark a chain supported based on balance queries alone.

**Completion:** each selected chain has a documented support matrix, adapter-contract and chain-specific tests, base-unit and error-handling coverage, and an opt-in testnet guide before release claims are made.

## 8. THORChain compatibility decision

- Inventory retained interfaces and obsolete SDK assumptions.
- Evaluate replacement with maintainable provider interfaces.
- Either restore the client with current tests or formally deprecate the reference package.

**Completion:** the package is supported with reproducible checks or unambiguously excluded from released functionality.

## 9. Packaging, documentation and releases

- Build and smoke-test each maintained package's wheel.
- Review versions, URLs, Python classifiers and changelogs.
- Explain the relationship to previously published PyPI distributions.
- Add runnable cross-chain examples using public fixtures, migration notes and API references.

**Completion:** a tagged release installs into a clean environment, its offline example runs, and users can identify precisely which workflows have been verified.

## Later exploration

Additional chain adapters, external signer interfaces, asynchronous provider pooling and higher-level cross-chain examples can follow stable client contracts. They are not current features.
